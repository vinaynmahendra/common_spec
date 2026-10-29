# Template: Area overview (`area`)

Generated from `area.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Frames one top-level area of the platform so every capability under it shares the same scope, principles and decisions.

**Depth:** 1–3 pages. Describe boundaries and rules, not implementation. If a paragraph starts describing how one capability works, move it into that capability's node. Revisit at each phase boundary.

**Default child template:** `standard`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose and scope (level 1)

Two or three sentences on why this area exists, then an explicit in-scope / out-of-scope list. Out-of-scope items should be things someone could reasonably expect to find here.

Illustrative example (not a requirement):

> Multi-tenancy makes every institution on the platform (HKIAC, a SEBI ODR institution, a CORD tenant) feel like it has its own system, while we run one codebase and one database per region.
> 
> **In scope:** tenant model, tenant resolution, data isolation, tenant lifecycle, tenant-level settings, data residency.
> **Out of scope:** user authentication (Platform Packages → Authentication), billing plans (Billing and Subscription), tenant-facing branding assets (Configuration and Customisation).

### `goals` Goals and non-goals (level 1)

3–6 measurable goals. Non-goals are deliberate exclusions, not negated goals.

Illustrative example (not a requirement):

> **Goals**
> - No query from the app role can return another tenant's row, proven by automated tests on every release
> - A new tenant can be provisioned in under 15 minutes without engineering involvement
> - Each tenant's data stays in its contracted region (India, Singapore, US)
> 
> **Non-goals**
> - Per-tenant databases
> - Tenant-specific code branches; variation is handled through configuration only

### `principles` Principles (level 1)

The rules every child node must follow. Short, imperative, testable.

Illustrative example (not a requirement):

> 1. Every tenant-owned table has a non-null `tenant_id` and a forced RLS policy
> 2. Tenant context is set per transaction, never per session
> 3. Cross-tenant reads happen only through the reporting role
> 4. Platform-level data (plans, tenant registry) never carries `tenant_id`

### `context` Context and boundaries (level 2)

Who and what this area talks to. A context diagram (Mermaid or ASCII) plus a table of neighbouring areas and what flows between them.

Illustrative example (not a requirement):

> | Neighbour | What flows | Direction |
> |---|---|---|
> | Authentication | Resolved tenant ID on every session | In |
> | Settings | Tenant-level overrides | Out |
> | Reporting | Read-only reporting role | Out |
> | Infrastructure | One Postgres per region | Depends on |

### `decisions` Key decisions (level 2)

Link Decision nodes and give one line on how each shapes the area. Do not restate the decision.

Illustrative example (not a requirement):

> - [19.1 Tenant isolation](#n-ADR-tenant-isolation) — shared DB with RLS; drives principles 1–3
> - [19.2 Next.js hosting](#n-ADR-next-js-hosting) — per-region containers make residency enforceable at deploy time

### `map` Capability map (level 2)

One line per child explaining what it owns. Shows gaps and overlaps at a glance.

Illustrative example (not a requirement):

> | Child | Owns |
> |---|---|
> | Tenant model | Hierarchy: platform → tenant → org unit → user |
> | Tenant resolution | Mapping a request to a tenant (subdomain, custom domain, header) |
> | Isolation strategy | RLS, roles, Prisma tenant context |
> | Tenant lifecycle | Onboard, suspend, offboard, export, delete |

### `phasing` Phasing (level 2)

Which children land in which implementation phase, and what must be true before the next phase starts.

Illustrative example (not a requirement):

> - **Phase 1:** tenant model, resolution, isolation, region pinning (exit: isolation tests green in CI in every region)
> - **Phase 2:** lifecycle, tenant settings
> - **Phase 4:** moving a tenant between regions (exit: rehearsed move of a test tenant)

### `risks` Risks and open questions (level 3)

Checklist of unresolved items and risks, each with an owner if known.

Illustrative example (not a requirement):

> - [ ] Custom domains need certificate automation per tenant — owner: DevOps
> - [ ] Confirm whether any client requires a dedicated database contractually

### `notes` Notes (level 3)

Reference material that does not fit elsewhere.

Illustrative example (not a requirement):

> Glossary: *Tenant* = a contracting institution. *Org unit* = a department or panel inside a tenant.

## Checks

### `ownership` Ownership and governance

**Question:** Is there one named accountable owner for this area, named reviewers for each specialist concern, and a defined way for changes to the area's scope or principles to be proposed and approved?

- Who is the single accountable owner (a person, not a team), and who is their deputy when they are unavailable?
- Who must review changes for each specialist concern that applies to this area: security, privacy / data protection officer, legal or operations, accessibility, infrastructure, the client-facing product lead for CORD, TERES or HKIAC CMP?
- Which engineering team builds and runs the children of this area, and does team ownership line up with the capability map (no child owned by two teams, no orphan children)?
- How is a change to scope, goals or principles proposed, who approves it, and how are child-node owners told?
- Which external parties have a say (for example a client institution whose contract fixes a requirement, an auditor whose finding must be closed)?
- When was this node last reviewed, and is the next review tied to a phase boundary in the Delivery plan?

**Good answer:** Named accountable owner and deputy, a reviewer list per specialist concern with names, a mapping of each child to one owning team, a stated change-approval route, and the date of last review with the next review linked to a phase gate.

**Red flags:**

- Owner given as a team or "engineering".
- No privacy or security reviewer for an area that handles tenant or personal data.
- Children owned by nobody or by two teams.
- No record of when the area was last reviewed.

### `boundaries` Scope and boundaries

**Question:** Are this area's boundaries with neighbouring areas sharp enough that every capability has exactly one home and every flow across the boundary has a named contract?

- For each out-of-scope item, which area does own it? Is there anything someone could reasonably expect here that no area owns?
- Does any capability appear, even partly, in two areas (for example notifications in both Platform Packages and Workflow, or audit in both Security and Observability)? How is the overlap resolved?
- For each neighbouring area in the context table, what crosses the boundary (API, domain events, shared database tables, files), and is there a contract node for each?
- Are any database tables shared with another area? If so, which area owns the schema and who may write to them?
- Which external systems does this area depend on (identity providers, payment gateways, MII interfaces, e-sign, cloud provider services), and is each covered by an Integration node?
- Is the context diagram consistent with the capability map and with the children actually in the tree?

**Good answer:** A context diagram at system-context level plus a table of neighbouring areas and external systems with what crosses each boundary and the node that defines the contract. Every out-of-scope item names its owning area, and any shared tables or overlapping capabilities are listed with a resolution.

**Red flags:**

- Out-of-scope items with no owning area.
- Two areas both claiming the same capability.
- Undocumented shared tables between areas.
- Context diagram that does not match the children in the tree.

### `principles` Principles and enforcement

**Question:** Is every principle short, testable and enforced by an automated check or a named review step, so child nodes cannot quietly break it?

- For each principle, how is compliance checked: a lint rule, a CI test (for example tenant-isolation tests on every new table), an architecture fitness test (for example forbidden imports between packages in the Turborepo), or a review checklist item?
- Which principles cover the platform's non-negotiables for this area: tenant isolation through forced RLS, data residency per region, audit of legally significant changes, accessibility, no secrets in code?
- Is any principle vague ("secure by design", "scalable") such that nobody could show it is broken? How would it be rewritten to be testable?
- Do any principles conflict (for example "one database per region" against a client asking for a dedicated database)? Which wins, and is the exception process stated?
- How are exceptions requested, approved, recorded and given an expiry date?
- Are principles reflected in the templates or scaffolding for child nodes, so new capabilities start compliant?

**Good answer:** Each principle is one imperative sentence with its enforcement mechanism (named CI check, lint rule, or review step) next to it. Conflicts between principles are resolved in writing, and an exception register exists with approver and expiry date.

**Red flags:**

- Principles with no enforcement mechanism.
- Aspirational statements that cannot be tested.
- Exceptions granted informally with no expiry.
- Principles that contradict a linked Decision node.

### `decisions` Decisions linked

**Question:** Are all decisions that shape this area recorded as Decision nodes with status, options considered and consequences, and are open decisions that block children called out?

- Which decisions constrain this area (for example shared database with RLS, Temporal self-hosted per region, ECS with an Azure Container Apps variant, Prisma tenant extension)? Is each linked with its status (proposed, accepted, superseded)?
- Does each linked decision record the options considered and why they were rejected, so the choice is not re-argued later?
- Which decisions are still open, which children are blocked until they are made, and what is the date by which each must be decided?
- Which decisions are driven by a specific client contract or regulator (for example a client requiring Azure, or data residency in India), and is that source cited?
- When was each decision last checked against reality (for example after a load test or an audit finding), and what would trigger revisiting it?
- Are there decisions made informally (in chat or meetings) that are being followed but never written down?

**Good answer:** A list of Decision nodes with status and a one-line effect on this area, a separate list of open decisions with the blocked children, decision owner and due date, and a stated trigger for revisiting each accepted decision. Client- or regulator-driven decisions cite their source.

**Red flags:**

- Key architecture choices that exist only in conversation.
- Open decisions with no owner or due date while children depend on them.
- Superseded decisions still linked as current.
- No record of alternatives considered.

### `compliance` Regulatory and control mapping

**Question:** Which regulations, standards and contractual obligations does this area carry, which controls does it implement, and which child node provides the evidence for each?

- Which obligations fall in this area, for example DPDP Act and Rules 2025, GDPR, Singapore PDPA, US state privacy laws, SEBI ODR circulars via MIIs, MSME reporting, AML / KYC / sanctions screening, FEMA, ISO 27001:2022, SOC 2, WCAG 2.2 AA, ISO 42001?
- For ISO 27001 Annex A controls and SOC 2 criteria relevant to this area, which child node implements each and what evidence does it produce (log, report, configuration, test result)?
- Which obligations differ by region or entity (NTPL India, TAPL Singapore, the US entity), and does the area state how those differences are handled?
- Which client contracts add obligations beyond law (for example HKIAC security schedules, SLA credits, audit rights, breach notice periods shorter than regulation)?
- Which obligations have a deadline that the Delivery plan must respect (for example DPDP Rules commencement dates, an audit window, a client go-live)?
- Who is the compliance owner for this area, and how is the mapping kept current when a regulation changes?

**Good answer:** A table mapping each obligation or control to the child node that implements it and the evidence produced, with region or entity differences marked. Contract-specific obligations and dated compliance deadlines are listed, and a named person keeps the mapping current.

**Red flags:**

- "Compliance is handled by the Regulatory area" with no mapping for this area.
- Controls listed without an implementing node or evidence.
- No awareness of region-specific obligations.
- Client contractual obligations not captured.

### `regions` Tenancy and residency

**Question:** How does this area behave across tenants and across the India, Singapore and US regions (and Azure where a client requires it), and which of its capabilities are per-region versus global?

- Which capabilities in this area run per region, and which (if any) are global (for example a control plane, tenant directory, billing, or a shared identity service)? What data do global parts hold?
- For any global part, how is it kept free of tenant personal data, or what transfer basis applies if it is not?
- What must differ when this area runs on Azure Container Apps instead of AWS ECS, and is that difference contained in the Infrastructure area?
- Which tenant-level variations does this area allow (configuration, feature flags, custom domains, dedicated resources), and where are they configured?
- How is a new region added: which children need changes, and how long would it take?
- Can a tenant be moved between regions, and if so, which children take part in the move?

**Good answer:** A list of per-region and global capabilities with the data each global part holds and its legal basis, the cloud-provider variation contained in named nodes, tenant variations with configuration sources, and the steps (or a linked node) for adding a region and moving a tenant.

**Red flags:**

- Global services that store tenant personal data with no transfer basis.
- Cloud-specific logic spread across many children.
- No position on adding a region or moving a tenant.
- Tenant variations implemented as code branches.

### `quality` Quality targets

**Question:** Does this area state measurable quality targets (availability, latency, recovery, capacity, security, accessibility) that child nodes inherit and that can be checked in production?

- What availability target applies (for example 99.9% per month per region), how is it measured, and does it match what client contracts promise?
- What recovery targets apply: recovery point objective (how much data can be lost) and recovery time objective (how long until service returns), per region? When were they last tested?
- What capacity must the area support at the end of the plan horizon (tenants per region, concurrent users, cases, documents, storage)?
- What latency targets apply to the main operations of this area?
- Which security and accessibility levels are required (for example OWASP ASVS Level 2, WCAG 2.2 AA), and how do children show they meet them?
- Which dashboards or service level objectives will show whether each target is being met?

**Good answer:** A short table of quality targets with numbers, measurement method and the service level objective or dashboard that tracks each, aligned with client contracts. Recovery targets are stated per region with the date of the last restore test.

**Red flags:**

- Targets described as adjectives ("highly available", "fast").
- Contract SLAs that exceed what the area commits to internally.
- Recovery objectives never tested.
- No capacity figures for the plan horizon.

### `phase` Phasing

**Question:** Is it clear which implementation phase each child capability lands in, what must be true before the next phase starts, and which children must not be deferred?

- Does every child in the capability map have a phase, and does the phasing match the Delivery plan node?
- Are the dependencies between children reflected in the order (for example tenant model before tenant lifecycle; isolation tests before any domain data)?
- Which children are cross-cutting and must exist from the first phase (audit, isolation, structured logging, accessibility) rather than being added later?
- What is the exit condition for this area at each phase, stated so it can be checked (for example "isolation tests green in CI in all three regions")?
- What is explicitly deferred, why, and what risk does deferral carry?
- Is the area reviewed at every phase boundary, and who signs off?

**Good answer:** Every child has a phase consistent with the Delivery plan, dependency order is explicit, cross-cutting children are in the first phase, and each phase has a checkable exit condition for this area. Deferred items are listed with the risk accepted and who accepted it.

**Red flags:**

- Children with no phase.
- Phasing that contradicts the Delivery plan.
- Security, audit or isolation deferred to a later phase.
- Exit conditions that cannot be checked.

