# Template: Design note (`design`)

Generated from `design.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Explains how something will be built when the approach involves trade-offs across several nodes, before the cost of changing it is high.

**Depth:** Mini design note 1–3 pages for a contained problem; full design note 10–20 pages for a large one. Split if it grows beyond that. Do not write one when the solution is obvious or when it would only be an implementation manual.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `context` Context and scope (level 1)

Objective background: what exists, what is being built. Facts, not requirements.

Illustrative example (not a requirement):

> Workflow logic, business decisions, the work itself and the runtime change at different speeds and are owned by different people. Temporal provides only the runtime.

### `goals` Goals and non-goals (level 1)

What the design must achieve, and things it deliberately will not do.

Illustrative example (not a requirement):

> **Goals:** tenant-specific procedures without code forks; rule changes without deploys; running cases unaffected by changes.
> **Non-goals:** a visual BPMN editor in phase 1.

### `design` Design (level 1)

Overview first, then detail. Diagrams, API sketches and data shapes at the level that matters. Focus on trade-offs.

Illustrative example (not a requirement):

> Five layers: process definition, decisions, work execution, runtime, integration and control, each mapped to Temporal roles. (See the 7.6 node for the full table.)

### `examples` Worked examples (level 2)

Concrete walk-throughs, code sketches.

Illustrative example (not a requirement):

> Hearing reminder across all five layers, with the decision table, activities, workflow and client calls.

### `alternatives` Alternatives considered (level 2)

Other reasonable designs and the trade-offs that led to this one.

Illustrative example (not a requirement):

> Camunda (BPMN + DMN + Zeebe) gives the layers out of the box but adds a Java-centric platform and licence cost for self-managed production.

### `crosscutting` Cross-cutting concerns (level 2)

Security, privacy, tenancy, observability, cost: how the design addresses each.

Illustrative example (not a requirement):

> Payload encryption via Payload Codec; tenant context through interceptors; search attributes for tenant and case.

### `guardrails` Guardrails (level 2)

Rules implementers must follow.

Illustrative example (not a requirement):

> Workflows contain flow only; definitions and rule versions are loaded once at start.

### `ownership` Ownership (level 3)

Who owns which part and how it changes.

Illustrative example (not a requirement):

> Process definitions (code): platform engineering. Decision tables: legal / operations per tenant.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Rules engine choice: in-house evaluator vs GoRules Zen vs FEEL interpreter

## Checks

### `security` Security and privacy

**Question:** What new attack surface and personal-data processing does this design introduce, and how is each threat addressed?

- Is there a data-flow diagram with trust boundaries (browser, Next.js server, workers, Temporal, Redis, Postgres, third parties)?
- Has a threat model been done (for example STRIDE) and where are the threats and mitigations listed?
- How are users and services authenticated and authorised at each hop, including Temporal workers and BullMQ jobs that run outside a user request?
- Which personal or confidential data does the design store or move, and is each item necessary (data minimisation)?
- How are data encrypted in transit and at rest, including Temporal payloads (payload codec) and Redis job data?
- Where are secrets and keys held, and who can access them?
- Does the design change any privacy notice, DPIA or records of processing?

**Good answer:** Includes a data-flow diagram with trust boundaries, a threat list with mitigations and owners, the authorisation model at each hop including background work, and a data inventory with encryption at rest and in transit. Notes which privacy records must be updated.

**Red flags:**

- No threat model for a design that adds an external interface or new data store
- Background jobs or workflows run with unrestricted service credentials
- Sensitive data in Temporal history or Redis without encryption

### `tenancy` Tenancy

**Question:** How is the tenant identity carried through every component, and what guarantees one tenant can never see or affect another's data or capacity?

- How does tenant context flow from request to Prisma transaction (set_config per transaction) and stay correct under PgBouncer transaction pooling?
- For any new table, is forced RLS enabled with a tenant_id policy, and does the application role lack BYPASSRLS?
- How is tenant context carried into Temporal workflows and activities, BullMQ jobs, caches, search indexes and object storage keys?
- What happens when tenant context is missing: does the operation fail closed?
- Are there any cross-tenant operations (platform admin, reporting, billing), and how are they isolated, authorised and logged?
- How does the design prevent one tenant's load from degrading others (per-tenant rate limits, queue fairness, Temporal task queue partitioning)?
- Which automated tests prove isolation across every new data path?

**Good answer:** Traces tenant context through each component, confirms forced RLS on every new table and fail-closed behaviour when context is missing, describes how cross-tenant admin paths are controlled, and covers noisy-neighbour protection. Names the automated cross-tenant tests and where they run.

**Red flags:**

- Isolation relies on developers remembering a WHERE tenant_id filter
- Cache or object storage keys without tenant prefix
- Background work picks up tenant from job payload without verification
- No noisy-neighbour controls for shared queues

### `residency` Data residency and lifecycle

**Question:** Does every piece of data the design creates stay in the tenant's region, and is it retained and deleted according to policy?

- Which stores (Postgres, Redis, Temporal, object storage, search, logs, backups) does the design write to, and are they all in the tenant's region?
- Does any component run centrally (for example a global admin, analytics or email service) and what tenant data does it see?
- What is the retention period for each new data type, and how is deletion implemented, including backups and Temporal history?
- How does the design support erasure and access requests under DPDP, GDPR and PDPA?
- If a tenant is moved between regions or offboarded, how is its data exported and removed?

**Good answer:** Lists each store with its region, retention period and deletion mechanism, identifies any central component and proves it holds no tenant personal data (or justifies it), and explains support for subject requests and tenant offboarding.

**Red flags:**

- A central service in one region processes all tenants' personal data
- No retention or deletion plan for new data
- Backups or workflow history ignored in deletion

### `failure` Failure handling and recovery

**Question:** What happens when each dependency fails or work is interrupted, and can the system recover without losing or duplicating case actions?

- For each external call and dependency, what are the timeout, retry policy and maximum attempts?
- Are operations idempotent (idempotency keys, unique constraints) so retries by Temporal or BullMQ cannot double-send notices or double-charge?
- Which steps are long-running and therefore in Temporal, and which are short jobs in BullMQ? Is that split justified?
- What happens to in-flight workflows during a deployment, including workflow versioning?
- What are the recovery point and recovery time objectives (RPO and RTO) for the data and workflows involved, and how were they tested?
- How are partial failures surfaced to users and operators (dead-letter queues, compensating actions)?

**Good answer:** Gives a dependency failure table (timeout, retry, fallback), shows idempotency for every side effect, explains the Temporal versus BullMQ placement, covers workflow versioning during deploys, and states tested RPO and RTO.

**Red flags:**

- Retries on non-idempotent side effects such as sending notices or emails
- No plan for in-flight workflows when code changes
- RPO and RTO unstated for case data

### `scale` Capacity, performance and cost

**Question:** Will the design meet its performance targets at expected and peak load per region, and what will it cost to run?

- What load is expected per region now and in 24 months (tenants, cases, documents, requests per second, peak events such as filing deadlines)?
- What are the latency and throughput targets, and what evidence (load test, benchmark) shows they can be met?
- Which component becomes the bottleneck first (Postgres connections behind PgBouncer, Redis memory, Temporal history size, ECS task limits)?
- Are queries designed with indexes that lead with tenant_id where RLS applies, and has query performance been checked under RLS?
- What is the estimated monthly running cost per region and per tenant, and how does it grow?
- Are there limits (file size, page size, rate limits) and are they enforced?

**Good answer:** States load assumptions per region, targets, the first bottleneck and how it is handled, evidence from a test or benchmark, enforced limits, and a cost estimate per region and per tenant.

**Red flags:**

- No load assumptions or targets
- Performance asserted without measurement for a hot path
- Running cost unknown

### `observability` Observability

**Question:** How will we know in production that the design works, is healthy and is meeting its objectives, per tenant and per region?

- Which service level indicators and objectives (SLIs and SLOs) apply, and how are they measured?
- Are traces propagated across Next.js, workers, Temporal and BullMQ with tenant and case identifiers as attributes (without personal data)?
- Which metrics and dashboards will exist, and which alerts page someone versus create a ticket?
- How are logs kept free of personal data and secrets, and kept in-region?
- What audit events (who did what to which case) does the design emit, and where are they stored?
- Is there a runbook for each alert?

**Good answer:** Defines SLIs and SLOs, the tracing and tenant-tagging approach, specific alerts with severity and runbooks, PII-free in-region logging, and the audit events emitted.

**Red flags:**

- No SLOs or alerts defined for a user-facing path
- Logs contain personal data or are shipped to another region
- Audit events for case actions missing

### `rollout` Rollout and migration

**Question:** How will the design be introduced safely, including data migration, and how is it rolled back if it goes wrong?

- Is the rollout behind a feature flag, per tenant or per region, and what is the order?
- Are database migrations backward-compatible (expand, migrate, contract) so old and new code can run together?
- How is existing data backfilled, verified and reconciled?
- What is the rollback plan at each stage, and has it been rehearsed?
- Which tenants or institutions must be told in advance, and does any contract require notice of change?

**Good answer:** Gives a staged rollout plan with flags and order, backward-compatible migrations, a backfill and reconciliation approach, a rehearsed rollback per stage, and a client communication plan where needed.

**Red flags:**

- Big-bang release with no flag or staged rollout
- Destructive migration in the same release as code change
- No rollback plan

### `reversibility` Reversibility

**Question:** Which parts of the design are hard to change later, and have those parts been decided deliberately and recorded?

- Which choices become expensive to change once data or integrations depend on them (data model, identifiers, API contracts, event formats, vendors)?
- Have those choices been recorded as ADRs and linked?
- Are public or tenant-facing contracts versioned, with a deprecation policy?
- What abstractions keep vendor-specific parts (for example AWS versus Azure) replaceable, and at what cost?
- What would we do differently if load or client requirements doubled?

**Good answer:** Lists the hard-to-reverse choices with links to their ADRs, explains contract versioning and deprecation, and identifies where abstractions keep cloud or vendor choices replaceable.

**Red flags:**

- Hard-to-reverse choices made inside the design note without an ADR
- Unversioned external APIs or event formats

