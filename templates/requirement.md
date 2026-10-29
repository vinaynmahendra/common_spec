# Template: Requirement (`requirement`)

Generated from `requirement.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** States one testable requirement precisely enough that two engineers would implement it the same way and a tester can verify it.

**Depth:** A few lines to half a page. One requirement per node. It should be necessary, unambiguous, singular, feasible and verifiable. Use EARS sentence patterns. If it needs a table, it is probably a Decision; if it needs steps, it is probably a Workflow.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `statement` Statement (level 1)

One sentence in EARS form. Patterns — Ubiquitous: "The <system> shall <response>." Event: "When <trigger>, the <system> shall <response>." State: "While <state>, the <system> shall…" Unwanted: "If <condition>, then the <system> shall…" Optional: "Where <feature>, the <system> shall…"

Illustrative example (not a requirement):

> When a database transaction starts for an authenticated request, the data-access layer shall set `app.tenant_id` to the request's tenant for that transaction only.

### `rationale` Rationale and source (level 1)

Why it is needed and where it comes from.

Illustrative example (not a requirement):

> Required by the tenant isolation decision (19.1) so that Postgres RLS policies apply to every query, including those written by mistake without a tenant filter.

### `acceptance` Acceptance criteria (level 1)

Given / When / Then scenarios, including the negative case.

Illustrative example (not a requirement):

> - Given a request for tenant A, when it reads `cases`, then only tenant A rows are returned
> - Given a pooled connection previously used by tenant A, when tenant B's request uses it, then `app.tenant_id` equals B
> - Given no tenant context, when a query runs, then it fails rather than returning rows

### `verification` Verification method (level 2)

Test, inspection, analysis or demonstration, and where the test lives.

Illustrative example (not a requirement):

> Integration test `tenant-context.spec.ts` against Postgres + PgBouncer in transaction mode; runs in CI on every PR.

### `priority` Priority (level 2)

MoSCoW or must/should/could, and the phase.

Illustrative example (not a requirement):

> Must, phase 1.

### `questions` Open questions (level 3)

Unresolved items as a checklist, each with an owner in brackets. Move answered items into the relevant section and delete them here.

Illustrative example (not a requirement):

> - [ ] Is the 30-day award deadline counted in calendar or working days for SEBI ODR matters? (Legal)
> - [ ] Does this apply to tenants on the Starter plan? (Product)

### `notes` Notes (level 3)

Anything else.

Illustrative example (not a requirement):

> Uses `set_config(..., true)` so the setting is transaction-scoped.

## Checks

### `necessary` Necessary

**Question:** Would anything important break, or any obligation go unmet, if this requirement were removed?

- Which parent capability, client commitment, regulation or policy fails without it?
- Is it a real need or a design choice written as a requirement (does it say how instead of what)?
- Does it duplicate another requirement in the tree?
- Is the priority (must, should, could) consistent with the consequence of leaving it out?

**Good answer:** Names the specific failure or unmet obligation if it is removed, confirms it is not a duplicate, and states what is needed rather than how to build it, unless the how is itself the constraint (with the reason).

**Red flags:**

- Requirement exists 'because it is good practice' with no source
- Duplicates or near-duplicates another node
- Implementation detail stated as a requirement without justification

### `unambiguous` Unambiguous

**Question:** Would two engineers and a tester read this requirement the same way?

- Does it use the EARS pattern that fits (ubiquitous, event, state, unwanted, optional), with one trigger and one response?
- Are vague words removed or quantified: 'fast', 'secure', 'user-friendly', 'appropriate', 'as needed', 'etc.', 'and/or'?
- Are all terms defined in the glossary or domain model (for example, 'case', 'party', 'tenant', 'filing')?
- Is the actor or system named precisely (which service or layer), and is 'shall' used for mandatory behaviour?
- Are units, time zones and limits stated (for example 'within 5 seconds at the 95th percentile', 'business days in the tenant's time zone')?

**Good answer:** The statement follows one EARS pattern, names the responsible component, contains no vague terms, and defines numbers with units, percentiles and time zones where relevant.

**Red flags:**

- Contains unquantified terms such as 'quickly' or 'securely'
- Uses 'and/or', 'etc.' or 'should' where behaviour is mandatory
- Subject is 'the system' when several components could be meant

### `singular` Singular

**Question:** Does the requirement state exactly one capability or constraint?

- Does the statement contain 'and', 'or', 'also', or a list of behaviours that could be tested separately?
- Could part of it pass while another part fails? If so, split it.
- Are conditions folded in that should be their own unwanted-behaviour requirement (if X, then...)?
- If it needs a table it is probably a Decision; if it needs steps it is probably a Workflow. Is the template right?

**Good answer:** One trigger, one response, one verifiable outcome. Any additional behaviours have been split into sibling requirements and linked.

**Red flags:**

- Two or more independently testable behaviours in one sentence
- Steps or decision tables embedded in a requirement

### `complete` Complete and scoped

**Question:** Does the requirement say everything needed to implement it, including when it applies, to whom, and what happens in the error case?

- Does it state which tenants, regions, products (CORD, TERES), roles and rule sets it applies to, or that it applies to all?
- Is the negative or unwanted case covered (missing tenant context, invalid input, dependency down)?
- Are boundaries stated (maximum sizes, empty values, limits, time windows)?
- Are performance, security or audit qualities that apply to this behaviour stated here or linked?
- Are there any 'TBD' items, and is each tracked with an owner and date?

**Good answer:** States its scope (tenants, regions, roles, products), includes at least one negative acceptance criterion, defines boundaries, and has no unowned TBDs.

**Red flags:**

- Only the happy path is described
- Scope across regions or tenants unstated where behaviour differs
- Open TBDs with no owner

### `feasible` Feasible

**Question:** Can this be built and run with our stack, budget and timeline, and without conflicting with platform constraints?

- Is it achievable with the chosen stack (Prisma, Postgres with forced RLS, PgBouncer transaction pooling, Temporal, BullMQ, ECS or Azure Container Apps)?
- Does it rely on a feature that behaves differently under transaction pooling or RLS (for example session-level settings, LISTEN/NOTIFY)?
- Is any numeric target realistic, based on a measurement or similar system?
- Does it depend on a third party (MII, payment provider, sanctions screening vendor) that guarantees what is needed?
- Has an engineer who would build it reviewed it?

**Good answer:** Confirms technical feasibility with the stack, names any risky dependency and its guarantee, cites evidence for numeric targets, and records engineering review.

**Red flags:**

- Target picked without evidence and never checked by engineering
- Requires session state that PgBouncer transaction pooling will break
- Depends on a vendor capability not in the contract

### `verifiable` Verifiable

**Question:** Is there a defined test, inspection, analysis or demonstration that clearly passes or fails, including the negative case?

- Which verification method applies (test, inspection, analysis, demonstration) and why?
- Do the Given/When/Then criteria include at least one negative case?
- Where does the test live, and does it run automatically in CI on every relevant change?
- Does the test environment reproduce the conditions that matter (real Postgres with RLS, PgBouncer in transaction mode, Temporal test server)?
- For quality targets, how is the measurement taken and over what period?
- For compliance requirements, what evidence will an auditor see (test report, log, screenshot, configuration export)?

**Good answer:** Names the method, the test file or procedure, the environment it runs in, and the pass condition including a negative case. For compliance-driven requirements, names the evidence artefact retained for ISO 27001 or SOC 2 audits.

**Red flags:**

- Acceptance criteria cannot fail (for example 'system handles errors gracefully')
- Test uses mocks that hide the behaviour under test (for example no RLS in test database)
- No negative case

### `consistent` Consistent

**Question:** Does this requirement agree with its parent, its siblings and the platform decisions, without conflicting terms or targets?

- Does it conflict with any sibling requirement or with the parent's acceptance criteria?
- Does it contradict an Approved ADR or design guardrail?
- Are terms and numbers the same as elsewhere (same timeout, same role names)?
- Do regional variations conflict (for example a retention period that differs between DPDP and GDPR tenants), and is the resolution stated?

**Good answer:** Confirms no conflicts with parent, siblings and ADRs, uses the glossary's terms, and states how any regional or regulatory differences are resolved.

**Red flags:**

- Contradicts an Approved ADR without raising it
- Same concept named differently across siblings

### `traced` Traced

**Question:** Is the source recorded, and can we trace forward from this requirement to the design, code and tests that satisfy it?

- What is the source: client contract clause, regulation section (for example DPDP Rules, SEBI ODR circular), ISO 27001 control, internal policy, or parent node?
- Is the exact clause or reference recorded, not just the name of the regulation?
- Which design, ADR and implementation items satisfy it (forward trace)?
- Which test or evidence verifies it?
- If the source changes (a new circular or contract amendment), how would we find this requirement?

**Good answer:** Records the source with a specific clause or reference and links forward to design nodes, code or tickets and verification tests, so a regulator or client audit can follow it both ways.

**Red flags:**

- Source recorded only as 'compliance' or 'client'
- No link to the test that proves it
- Regulatory requirement with no clause reference

