# Template: Workflow / process (`workflow`)

Generated from `workflow.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies a long-running or multi-step process: what starts it, every step and wait, who acts, and what happens when things fail or rules change mid-flight.

**Depth:** 3–8 pages. Every step, timer and human input must appear in the sequence; implementers should not invent behaviour. Failure handling is mandatory for Approved. Tenant-specific timings are referenced to a Decision node, not hard-coded here.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose and outcome (level 1)

What the process achieves and what "done" means.

Illustrative example (not a requirement):

> Ensures every scheduled hearing has a confirmed neutral, or escalates to the tribunal secretary in time to re-arrange. Done = hearing confirmed or escalation task created.

### `trigger` Trigger and inputs (level 1)

What starts it (event, user action, schedule), inputs, and the workflow ID convention.

Illustrative example (not a requirement):

> Started on `hearing.scheduled`. Inputs: hearingId, hearingAt, facts {tenant, caseType, claimValue}, policyVersion. Workflow ID: `{tenantId}-hearing-reminder-{hearingId}` (re-scheduling the hearing signals the same workflow, never starts a second).

### `actors` Actors (level 1)

Humans and systems that act in the process, and how each interacts (signal, update, task).

Illustrative example (not a requirement):

> | Actor | Interaction |
> |---|---|
> | Neutral | Confirms via portal → `neutralConfirmed` signal |
> | Tribunal secretary | Receives escalation task |
> | Scheduler | Sends `hearingRescheduled` signal |

### `steps` Step sequence (level 1)

Ordered steps with type (decision, activity, timer, signal wait, child workflow). Diagram for anything with branches.

Illustrative example (not a requirement):

> 1. **Decision** `hearing-reminder-policy` → reminderDays, confirmWithinHours
> 2. **Timer** until hearingAt − reminderDays
> 3. **Activity** sendReminder (Notifications)
> 4. **Wait** for `neutralConfirmed` or timeout confirmWithinHours
> 5. **Activity** escalateToSecretary (creates human task) if timed out

### `timers` Timers and SLAs (level 1)

Every deadline, its source (rule, regulation, contract) and what happens at breach.

Illustrative example (not a requirement):

> | Timer | Value | Source | On breach |
> |---|---|---|---|
> | Reminder lead | 3–7 days | Decision table per tenant | — |
> | Confirmation window | 24–48 h | Decision table | Escalate |
> | SEBI ODR arbitrator appointment | 5 calendar days from reference (illustrative; confirm against the current circular) | SEBI ODR circular | Alert compliance |

### `signals` Signals, updates and queries (level 2)

Every external input and state query, with payload and validation.

Illustrative example (not a requirement):

> | Name | Kind | Payload | Validation |
> |---|---|---|---|
> | neutralConfirmed | Signal | {userId} | Must be the appointed neutral |
> | hearingRescheduled | Signal | {hearingAt} | Restarts reminder timer |
> | status | Query | — | Returns current step and due time |

### `activities` Activities (level 2)

Each activity, its side effect, idempotency key, timeout and retry policy.

Illustrative example (not a requirement):

> | Activity | Idempotency key | Timeout | Retries |
> |---|---|---|---|
> | sendReminder | `{wfId}:reminder` | 1 min | 5, exp. backoff |
> | escalateToSecretary | `{wfId}:escalate` | 1 min | 5 |

### `failure` Failure, cancellation and compensation (level 2)

What happens on activity failure after retries, on cancellation, and which steps need undoing.

Illustrative example (not a requirement):

> - Notification provider down after retries → create ops alert, continue to wait step (escalation still protects the hearing)
> - Hearing cancelled → workflow cancelled; no compensation needed
> - Neutral withdraws after confirming → handled by Neutrals replacement workflow (child), not here

### `versioning` Versioning (level 2)

How running instances behave when the code or rules change.

Illustrative example (not a requirement):

> Policy version pinned at start (input). Code changes use Worker Versioning; in-flight reminders finish on the version they started.

### `observability` Visibility and monitoring (level 2)

Search attributes, metrics, alerts for stuck or failing instances.

Illustrative example (not a requirement):

> Search attributes: tenantId, caseId, hearingId, step. Alert if any instance sits in "escalate" step > 2 h without a task being created.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Should co-arbitrators each confirm, or the presiding arbitrator only?

## Checks

### `tenancy` Tenancy and residency

**Question:** Does every part of this workflow (ID, search attributes, activities, child workflows, task queues) carry the tenant, run only in the tenant's home region, and set the tenant on every database transaction it opens?

- What is the workflow ID convention, and does it include tenant ID and business key (for example `{tenantId}-case-intake-{caseId}`, matching the `{tenantId}-{process}-{entityId}` guardrail in 7.6) so that a duplicate start in the same tenant is rejected and two tenants can never collide? Which Workflow ID reuse and conflict policy is set?
- Which Temporal namespace and cluster does it run on? Since Temporal is self-hosted per region, how is a start request routed to the tenant's home region, and what stops a worker in one region from processing another region's tenant?
- Is tenantId a custom search attribute on every execution, so operators can list and act on one tenant's workflows only?
- Does every activity receive tenantId as an explicit input and open its Prisma transaction with that tenant set (forced RLS), rather than reading it from an ambient context that may be missing in a worker?
- Are there shared task queues across tenants? If yes, how is one noisy tenant (for example a bulk import of 10,000 SEBI ODR cases) prevented from starving others: per-tenant rate limits, priority, or separate queues?
- What happens to running workflows when a tenant is suspended or offboarded: paused, cancelled with compensation, or allowed to finish?
- What tenant and personal data is written into workflow history (inputs, results, signal payloads), and is it encrypted with a payload codec using keys held in the tenant's region?

**Good answer:** A stated workflow ID pattern containing tenant and business key, with the reuse / conflict policy; tenantId registered as a search attribute; every activity signature taking tenantId and setting it on the transaction; region routing described; and a fairness rule for shared queues. Workflow history holds IDs rather than document content where possible, and any personal data in payloads is encrypted with a regional key.

**Red flags:**

- Workflow IDs without tenant ID, or random UUIDs that allow duplicate runs for the same business key.
- Activities that query the database without setting the tenant (RLS bypassed by a privileged worker role).
- Full documents or personal data stored in workflow history unencrypted.
- No behaviour defined for running workflows when a tenant is suspended.

### `security` Access to workflow controls

**Question:** Who and what may start, signal, update, query, cancel, reset or terminate this workflow, and is each of those checked against the permission matrix before it reaches Temporal?

- For every signal and update listed in the Signals section, which role and case relationship may send it (for example only the presiding arbitrator may signal "order issued")? Where is that check made: in the API before calling Temporal, in an update validator, or both?
- Do update validators reject invalid or out-of-state input (for example extending a deadline that has already passed) so a bad request never enters history?
- Who has access to the Temporal Web UI and CLI in each region, and can they see payloads? Is the codec server restricted so operators see only what they are permitted to see?
- Which operator actions (reset, terminate, batch cancel) are allowed in production, who approves them, and are they audited outside Temporal?
- Do activities call external systems (e-sign, payment, email, MII APIs) with credentials scoped to the tenant, and where are those secrets fetched from?
- Can a user trigger the workflow repeatedly to cause cost or spam (for example resending notices)? What rate limits apply?

**Good answer:** A table of every external input (start, signal, update, query, cancel) with the permitted role and relationship and where the check runs, plus update validators for state-dependent input. Operator access to Temporal UI, CLI and codec server is restricted by role and region, and production reset or terminate actions need approval and are logged in the platform audit trail.

**Red flags:**

- Signals sent directly from the browser or from any authenticated user without a permission check.
- Open Temporal Web UI access with decoded payloads for all staff.
- Production terminate or reset with no approval or audit.
- Platform-wide credentials used by activities for tenant-specific integrations.

### `idempotency` Side effects and idempotency

**Question:** Can every activity be retried safely, so that retries, worker crashes and replays never send a notice twice, charge twice or file a document twice?

- For each activity with an external side effect (email or SMS to a party, payment capture, e-sign envelope, MII report submission, document generation), what idempotency key is used and is it passed to the external system?
- Where the external system has no idempotency support, how is a duplicate prevented: a check-then-act with a recorded outcome, or a dedup table keyed by workflow ID plus activity ID?
- Are start-to-close timeouts, schedule-to-close timeouts and heartbeat timeouts set for each activity, with values justified by the external system's behaviour? Long activities (transcription, eBundling) must heartbeat.
- Which errors are marked non-retryable (validation failures, permission denied, sanctions hit), so they fail fast instead of retrying for hours?
- Is workflow code free of non-deterministic calls (current time, random numbers, network, database) outside activities, and is this enforced by the SDK sandbox and lint rules?
- Do any short jobs belong on BullMQ instead of Temporal (or the reverse)? Is the boundary stated, and how is a hand-off between them made idempotent?

**Good answer:** A table of activities with side effect, idempotency key, timeouts, retry policy (initial interval, backoff, maximum attempts or expiry) and non-retryable error types. Every external side effect is either idempotent at the provider or protected by a recorded-outcome check, and long-running activities heartbeat.

**Red flags:**

- Default retry policy everywhere, with no non-retryable errors listed.
- Emails, payments or regulator submissions with no idempotency key.
- No timeouts stated, or a long activity with no heartbeat.
- Database or HTTP calls made directly from workflow code.

### `audit` Audit and legal record

**Question:** Which steps of this workflow are legally significant events, and how is each one recorded in the platform audit trail (not just in Temporal history, which is retained only briefly)?

- List the steps that create legal effect or evidence, for example notice served, deadline started, deadline expired, reminder sent, default noted, hearing scheduled, transcript certified, award dispatched.
- For each, which activity writes the audit record, with actor (person or system), tenant, case, timestamp, inputs and outcome? Is the write idempotent so a retry does not duplicate it?
- Which evidence must be kept for proof of service: message ID from the email or SMS provider, delivery and read receipts, bounce records, the exact content sent?
- When a person acts through a signal or update (for example secretariat extends a deadline), are their identity and reason captured in the payload and in the audit record?
- How long does the Temporal namespace keep closed workflow history, and is anything needed later kept elsewhere before it expires?
- When automated steps act on behalf of the institution (auto-reminders, auto-default), is that clearly recorded as a system action with the rule version that triggered it?

**Good answer:** A list of legally significant steps mapped to audit event types, with the writing activity, fields captured and evidence retained (for example provider message ID and delivery status for every notice). Human inputs carry actor and reason. The answer states Temporal's retention period and confirms the platform audit trail, not Temporal history, is the legal record.

**Red flags:**

- Relying on Temporal history as the audit trail.
- No proof-of-service evidence for notices with legal effect.
- Signals that change deadlines without recording who and why.
- Audit writes that duplicate on retry.

### `compliance` Regulatory timelines

**Question:** Which timers in this workflow come from regulation, institutional rules or contract, how are their values configured and versioned, and how is a breach detected and reported before it happens?

- For each timer in the Timers section, what is its source (for example SEBI ODR circular stage timelines, HKIAC rules, the DPDP Rules 72-hour breach report, an SLA in the tenant contract) and which Decision node holds the value?
- How are business days, public holidays and the seat's time zone applied, and where does the holiday calendar come from per jurisdiction?
- When a rule value changes (for example a regulator shortens a timeline), do running workflows keep the value they started with or pick up the new one? Is that choice stated per timer and recorded?
- Is there an early warning before breach (for example at 75% of elapsed time) to the responsible person, and an escalation path if nobody acts?
- What happens at breach: an automatic step, a human task, a report to the MII or institution? Is the breach recorded for regulatory reporting?
- Can a timer be paused or extended (stay of proceedings, extension granted by the tribunal)? Who can do it, and is the reason captured?
- Is there a report or dashboard showing every open regulatory deadline by tenant, and who watches it?

**Good answer:** Every regulatory or contractual timer has a cited source, a value held in a versioned Decision node, a time-zone and holiday rule, and a stated policy for in-flight rule changes. Breach handling includes pre-breach warning, escalation, the action on breach and a record feeding the Reporting node.

**Red flags:**

- Timer durations hard-coded in workflow code.
- No holiday or time-zone rule for deadlines with legal effect.
- Breach only discovered after the fact, with no warning or escalation.
- No way to pause or extend a deadline with a recorded reason.

### `change` Change and versioning safety

**Question:** How will this workflow be changed safely while instances are running for weeks or months, and how do we prove a change does not break them?

- What is the expected lifetime of one instance (a case workflow may run for over a year)? Is the workflow split (child workflows, continue-as-new) so that history stays under Temporal's limits and new code can take over at clear points?
- Which change mechanism is used: Temporal patching (patched / deprecatePatch), Worker Versioning, or starting new instances on a new workflow type? When does each apply?
- Is replay testing run in CI against a sample of real (anonymised) histories from production for every change to workflow code?
- How are rule and configuration changes (Decision node values) separated from code changes, and which version does a running instance use?
- How are old patches removed, and who tracks when no instances remain on an old version?
- If a bug is found mid-flight, what is the repair procedure: signal a correction, reset to a prior event, or cancel and restart with migration? Who approves?

**Good answer:** A stated versioning approach (patching or Worker Versioning) with the rule for when each is used, replay tests in CI using histories captured from each region, continue-as-new or child workflows for long-running cases, and a written repair procedure for in-flight bugs with approval. Rule versions are pinned or refreshed by explicit policy.

**Red flags:**

- No versioning approach for workflows that run longer than a release cycle.
- No replay tests, or replay tests only against synthetic histories.
- Unbounded history growth on long cases (no continue-as-new).
- Fixing stuck workflows by ad hoc terminate and restart.

### `observability` Observability and operations

**Question:** Can operators see, for every tenant and region, which instances are stuck, failing or about to breach a deadline, and are they alerted in time to act?

- Which custom search attributes are registered (tenantId, caseId, stage, nextDeadline, assignee) so operators can filter instances in the Temporal UI and through the visibility API?
- Which metrics are emitted: SDK and server metrics (schedule-to-start latency, activity failures, workflow task failures) plus business metrics (instances per stage, time in stage)?
- What counts as stuck for this workflow (for example no progress for 48 hours in a stage where the expected time is 4 hours, or an activity retrying for more than 1 hour), and which alert fires?
- Who is paged or notified for each alert, in which region, and during which hours? Is there a runbook link in the alert?
- Are traces propagated from the API request that started the workflow through activities to external calls (OpenTelemetry), with tenantId on spans and personal data excluded?
- Is there a per-tenant view the institution's secretariat can see (for example pending human tasks and upcoming deadlines) separate from the operator view?

**Good answer:** A list of search attributes, metrics and alerts with thresholds, each alert routed to a named on-call team with a runbook. Stuck is defined in measurable terms for this workflow, schedule-to-start latency is monitored per task queue and region, and traces link the start request to activities with tenantId and no personal data.

**Red flags:**

- No search attributes beyond defaults, so one tenant's instances cannot be found.
- Alerts only on infrastructure, none on business-level stuck states.
- No owner or runbook for alerts.
- Personal data in logs, metrics labels or span attributes.

### `humantasks` Human tasks

**Question:** For every step that waits on a person, is it clear who is asked, how they are told, how long they have, and what happens if they do not act or are no longer available?

- For each human wait, which role and case relationship receives the task, and how is the assignee resolved (named person, pool, round-robin)?
- How is the person notified (in-app task list, email, SMS) and are notifications accessible and in their preferred language?
- What is the reminder and escalation schedule, and what happens at final timeout: default action, escalation to a supervisor, or a recorded failure to act with legal effect?
- What happens if the assignee is removed (neutral recused, counsel withdraws, staff member leaves)? Is the task reassigned automatically, and is the reassignment audited?
- Can two people act on the same task at once? How is the second response rejected, and what does the person see?
- How does a person see why they are being asked and what each choice will do (especially for choices with legal effect)?

**Good answer:** A table of human waits with assignee rule, notification channel, reminder and escalation timings (from a Decision node), timeout outcome, and reassignment rule. Task completion is an update with validation so that only one response is accepted and the result is returned to the user immediately.

**Red flags:**

- Waits with no timeout, leaving instances stuck indefinitely.
- No reassignment when the assignee leaves the case.
- Human input via fire-and-forget signals with no validation or confirmation.
- Timeout outcomes with legal effect that nobody from legal or operations has approved.

### `testing` Testing

**Question:** How will we prove every path through this workflow, including timers, human waits, failures and compensation, behaves as specified without waiting real time?

- Are there time-skipping tests for every timer and SLA, including reminder, escalation and breach paths?
- Is every branch in the step diagram covered, including cancellation at each waiting point?
- Are activity failures injected (timeouts, non-retryable errors, external system down for hours) to prove retries, compensation and alerts behave as specified?
- Are activities tested on their own against real dependencies (Postgres with RLS, sandbox accounts for e-sign, payments and messaging) including idempotency on repeat calls?
- Is replay testing in CI against recorded histories mandatory before merge for workflow code changes?
- Is there an end-to-end test in staging that runs one realistic case through the workflow in each region?
- Are tenant-isolation tests included, for example a signal for tenant A's workflow sent with tenant B's credentials is rejected?

**Good answer:** Time-skipping tests for each timer, branch and cancellation point; failure-injection tests for each activity with compensation verified; activity tests against real Postgres with RLS and provider sandboxes; replay tests gating merges; and a per-region staging end-to-end run. Coverage is shown against the step list in this node.

**Red flags:**

- Only happy-path tests, or timers tested by real sleeps.
- No replay tests in CI.
- Compensation paths never exercised.
- Activities mocked everywhere, so idempotency and RLS behaviour are never tested.

