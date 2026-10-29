# Template: Decision record (`adr`)

Generated from `adr.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Records one architecturally significant decision with its context, the decision itself, its consequences and how we will confirm it is followed.

**Depth:** 1–2 pages. One decision per record. Short is a feature: a reader should understand the decision in two minutes. Once Approved, do not rewrite history; supersede with a new record and link it.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `context` Context and problem (level 1)

The situation and the question being decided, phrased as a question. Name the part of the system affected.

Illustrative example (not a requirement):

> Every tenant's data must be isolated, and some clients require their data to stay in India, Singapore or the US. How should tenant data be separated in Postgres?

### `drivers` Decision drivers (level 1)

Forces and criteria that matter: constraints, qualities, costs, team skills.

Illustrative example (not a requirement):

> - Provable isolation (tested in CI)
> - Operational simplicity for a small team
> - Works naturally with Prisma
> - Connection efficiency with PgBouncer
> - Region-level residency

### `decision` Decision (level 1)

The decision stated plainly, with justification tied to the drivers.

Illustrative example (not a requirement):

> Shared database per region with a `tenant_id` column on every tenant table and forced Postgres Row-Level Security. Tenant context is set per transaction through a Prisma Client extension. Chosen because it gives database-enforced isolation with one connection pool and one migration path.

### `consequences` Consequences (level 1)

What becomes easier and harder, from several stakeholders' points of view.

Illustrative example (not a requirement):

> **Easier:** one migration path; one pool per region; cross-tenant reporting via a dedicated role.
> **Harder:** every new table needs RLS (enforced by a lint check); noisy-neighbour load must be watched; a client demanding a dedicated database becomes a special project.

### `confirmation` Confirmation (level 2)

How we check the decision is implemented and stays followed.

Illustrative example (not a requirement):

> CI test suite asserts that, for every table with `tenant_id`, RLS is enabled and forced, and that a query under tenant A returns no tenant B rows.

### `options` Options considered (level 2)

Optional. Other options at the same level of abstraction and why they were not chosen, if useful to future readers.

Illustrative example (not a requirement):

> Schema-per-tenant was assessed; it needs one Prisma client or migration run per schema, which scales poorly in connections and migration time.

### `revisit` When to revisit (level 2)

Conditions that would reopen the decision.

Illustrative example (not a requirement):

> A contract requiring physical database separation, or a single tenant exceeding 30% of a region's load.

### `questions` Open questions (level 3)

Unresolved items as a checklist, each with an owner in brackets. Move answered items into the relevant section and delete them here.

Illustrative example (not a requirement):

> - [ ] Do we need a second region for Temporal before Singapore go-live? (Platform)
> - [ ] Who signs off the revisit trigger: CTO or Architecture forum? (Governance)

### `notes` More information (level 3)

Links, benchmarks, meeting notes.

Illustrative example (not a requirement):

> See Multi-tenancy → Isolation strategy; Infrastructure → Database connection handling.

## Checks

### `significance` Significance

**Question:** Is this decision architecturally significant enough to need a record, and is the scope of what it decides clear?

- Is it hard or expensive to reverse once code depends on it (estimate the effort to undo after 6 and 18 months)?
- Does it affect more than one team, service, product (CORD, TERES) or region?
- Does it touch a quality we are accountable for externally: tenant isolation, data residency, security, auditability, availability?
- Is it one decision? If the record decides two things, should it be split?
- Is the context phrased as a neutral question, not already presuming the answer?
- Which parts of the system are explicitly out of scope of this decision?

**Good answer:** States in one or two sentences why the decision is significant (cost to reverse, breadth, external commitments) and what it does and does not cover. The question in the context section could be answered by any of the options without rewording.

**Red flags:**

- A routine implementation choice dressed up as an ADR, or a significant one handled in chat only
- Two or more independent decisions in one record
- Context written to justify a pre-chosen answer

### `options` Options and evidence

**Question:** Were genuinely different options compared against the same drivers, and are the claims behind the choice backed by evidence?

- Are at least two realistic options described at the same level of abstraction, including 'do nothing' or 'keep current approach' where relevant?
- Is each option scored against every listed driver, not just the winner's strengths?
- Which claims rest on evidence (spike, benchmark, load test, vendor documentation, cost quote) and which are assumptions? Are assumptions labelled?
- Are total costs compared: licences, hosting per region, operations effort, hiring and skills?
- For managed services or vendors, have lock-in, vendor viability and availability in all our regions (India, Singapore, US, and Azure where needed) been checked?
- Does the decision fit existing platform decisions (Prisma, forced RLS, PgBouncer transaction pooling, Temporal, BullMQ), or does it knowingly diverge?

**Good answer:** Shows a comparison of two or more options against the same weighted drivers, with each key claim linked to evidence or marked as an assumption. Includes rough multi-region cost and operations effort, and calls out any conflict with existing ADRs.

**Red flags:**

- Only one option considered
- Drivers chosen after the decision to favour it
- Performance or cost claims with no spike, benchmark or source
- Option unavailable in one of our residency regions and nobody checked

### `compliance` Regulatory, residency and tenancy fit

**Question:** Does the decision keep us within our data residency, tenant isolation and regulatory obligations, and has anyone accountable for those confirmed it?

- Does the decision change where tenant data is stored, processed, backed up or logged? Does it stay in the tenant's pinned region?
- Does it weaken or bypass tenant isolation (for example, a new data store without RLS, or a shared cache keyed without tenant_id)?
- Does it add a sub-processor or vendor that must be disclosed to clients or added to data processing agreements?
- Which controls in ISO 27001:2022 Annex A, SOC 2 criteria, DPDP, GDPR, PDPA or SEBI ODR circulars does it affect, and is the control owner aware?
- Does it change audit logging, retention or our ability to answer a regulator or institution's request?
- Has security or compliance reviewed it, and is that review recorded in the ADR?

**Good answer:** Says explicitly whether residency, isolation, sub-processors, retention and audit are affected, and how. Lists the affected controls by reference and records the security or compliance reviewer and date.

**Red flags:**

- Residency or tenancy impact not mentioned for a decision about data or infrastructure
- New vendor or sub-processor with no disclosure plan
- No security or compliance review for a decision that touches personal data

### `consequences` Consequences and costs

**Question:** Are the downsides as clearly stated as the benefits, from the viewpoint of each group that lives with the decision?

- What becomes harder or slower for developers, operations, security, support, and tenants' users?
- What new failure modes, operational duties or on-call load does it introduce?
- What technical debt or follow-up work does it create, and is that work ticketed with an owner?
- What does it cost to run per region per month, roughly, and how does that scale with tenants?
- Who must learn something new, and is there a plan for that?

**Good answer:** Lists positive and negative consequences per stakeholder group, including operational and cost effects and new failure modes, with follow-up work linked to tracked tickets.

**Red flags:**

- Consequences section lists only benefits
- Follow-up work mentioned but not ticketed or owned
- Operational cost or on-call impact ignored

### `reversibility` Reversibility and revisit triggers

**Question:** If this decision turns out wrong, how would we find out, and what would it cost to change course?

- What observable signals would tell us the decision is failing (measurable thresholds where possible)?
- What specific conditions would reopen it: scale, a new region, a client requirement (for example Azure-only), regulation change, vendor price change?
- What is the exit path and rough effort to migrate away?
- Can the decision be made more reversible now (an interface, abstraction or adapter) at acceptable cost?
- When is the next scheduled review date, if any?

**Good answer:** Names measurable revisit triggers, an outline exit path with rough effort, and any cheap steps taken to keep the decision reversible.

**Red flags:**

- 'Revisit if needed' with no concrete trigger
- No idea of the exit cost for a hard-to-reverse vendor or data decision

### `confirmation` Confirmation

**Question:** Is there an automated or scheduled check that the decision is actually implemented and keeps being followed?

- What mechanism checks compliance: lint rule, architecture test, CI policy, schema check, infrastructure policy-as-code, or scheduled review?
- Where does the check live and does a failure block merge or deployment?
- For decisions that cannot be automated, who reviews compliance and how often?
- How are permitted exceptions recorded and approved?
- How will we know the check itself still works (for example, a deliberately failing test case)?

**Good answer:** Names the concrete check (for example, a CI test that fails if a table lacks forced RLS, or a dependency rule that blocks direct Postgres access outside the data layer), where it lives, that it blocks on failure, and how exceptions are approved.

**Red flags:**

- Confirmation is 'code review' with no specific check
- Check exists but does not block merge or deployment
- No route for recording exceptions

### `linked` Linked and lifecycle

**Question:** Is the record linked to every node it governs and to related decisions, with a clear status and supersession trail?

- Are all affected spec nodes linked with 'Decided by', and do those nodes link back?
- Which earlier ADRs does this depend on, conflict with or supersede, and are those records updated with a link rather than edited?
- Is the status current (Proposed, Accepted, Superseded, Deprecated) with dates and deciders named?
- Were the people who must live with the decision consulted and informed, and is that recorded?
- Is the record discoverable where engineers work (same repository or workspace) with a stable ID?

**Good answer:** Lists linked nodes and related ADRs both ways, shows status with dates and named deciders, consulted and informed groups, and marks any superseded record without rewriting its history.

**Red flags:**

- Affected nodes not linked, so implementers never see the decision
- Approved record edited in place instead of superseded
- No named decider

