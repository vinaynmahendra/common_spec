---
id: "ADR"
title: "Decisions"
parent: null
order: 19
type: "area"
template: "area"
childTemplate: "adr"
status: "draft"
owner: null
indicative: false
summary: "Technology and architecture decisions, one node per decision."
links: []
rev: 4
syncHash: "a9e90296b08da401"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T09:00:00Z"
updatedBy: null
---

# 19 Decisions

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Technology and architecture decisions, one node per decision.

<!-- section:purpose -->
## Purpose and scope

Records each platform decision with its context and consequences. Capabilities link to the decisions that shape them.

This area is the platform's decision log, chaired by the architecture review board (ARB). It holds one node per architecturally significant decision, using the Decision record template. The ADR process itself (when a record is needed, review and approval, PR template hooks) is owned by [[FND-governance]]; architecture documentation and runbooks live in [[DOC-architecture-docs-adrs-runbooks]].

**In scope**

- Technology choices with platform-wide effect (ORM, workflow engine, queue, hosting, orchestration)
- Architecture patterns that every capability must follow (tenant isolation, aggregator reporting mechanism)
- Open decisions awaiting a choice, recorded as Proposed records so that blocked nodes can link to them
- Supersession history: replaced decisions stay readable

**Out of scope**

- Library choices inside one package (owned by that package node, within [[APP-framework-dependencies]])
- Coding standards and conventions ([[FND-language-and-conventions]])
- Product and commercial decisions (pricing, plans: [[BIL-plans-entitlements-and-usage]])
- Security control design ([[SEC-isms-controls]]); a decision record may reference controls but does not define them

<!-- section:goals -->
## Goals and non-goals

**Goals**

1. Every decision that would cost more than about two engineer-weeks to reverse, or that clients will see in a security or residency review, has a record before implementation starts.
2. A new engineer can understand any decision in about two minutes from its record.
3. Every record names how it is confirmed (an automated check or a scheduled review) and what would reopen it.
4. Every capability node links to the decisions that constrain it, and every decision lists the nodes it governs.
5. Open decisions that block a phase are visible, with an owner and a due date, before that phase starts ([[PLAN]]).

**Non-goals**

- Recording every small design choice; those belong in the capability node's design section.
- Replacing the capability nodes' detail; a record states the choice and points to where it is implemented.

<!-- section:principles -->
## Principles

| # | Principle | Enforced by |
|---|---|---|
| P1 | One decision per record; the question in the context section must be answerable by every option listed | ARB review checklist |
| P2 | Approved records are not rewritten; a change is a new record that supersedes the old one, with links both ways | Workspace status rules; ARB |
| P3 | Every record states residency, tenant isolation and regulatory effects, even if "none" | Template check `compliance`; ARB |
| P4 | Every record has a confirmation mechanism; an automated check is preferred over a manual review | Template section `confirmation`; ARB refuses approval without it |
| P5 | Revisit triggers are measurable where possible (a number, a contract event, a vendor change) | ARB review checklist |
| P6 | Numbers in a record are either measured (with a link) or labelled as an assumption | ARB review checklist |
| P7 | A capability may not contradict an Approved record; it either complies or raises a new record | Node review: reviewers check linked ADRs |

<!-- section:context -->
## Context and boundaries

```
   capability nodes (MT, PKG, WF, INF, AI, RPT ...)
            |  link to the decisions that shape them
            v
   +-------------------------+       proposes / approves       +-----------------------+
   |  Decisions area (ADR)   | <------------------------------ | Architecture review   |
   |  one record per choice  |                                 | board (FND-governance)|
   +-------------------------+ ------------------------------> +-----------------------+
            |  confirmation checks run in              records outcome
            v
   CI pipelines (DEP), tests (TST), IaC policy checks (INF)
```

| Neighbour | What crosses the boundary |
|---|---|
| [[FND-governance]] | The ADR process, PR template prompt "does this need an ADR?", CODEOWNERS for this area |
| [[PLAN]] | Open decisions that block a phase appear as plan dependencies |
| [[DEP-ci-cd-pipelines-build-test]], [[TST-multi-tenant-isolation-tests]], [[INF-cloud-and-iac]] | Host the automated confirmation checks named in each record |
| [[SEC-isms-controls]], [[AI-ai-governance-and-impact]] | Controls referenced by records; ISO 27001 and ISO 42001 evidence of change management |
| [[DOC-architecture-docs-adrs-runbooks]] | The arc42 overview links to this area for its "architecture decisions" section |

<!-- section:decisions -->
## Key decisions

| # | Record | Status | Effect on the platform |
|---|---|---|---|
| 19.1 | [[ADR-tenant-isolation]] | Approved | Every tenant table has `tenant_id` and forced RLS; shapes [[MT-isolation-strategy]] and all schemas |
| 19.2 | [[ADR-next-js-hosting]] | Approved | Web tier runs as self-hosted containers per region; shapes caching and release |
| 19.3 | [[ADR-orm]] | Approved | Prisma is the only database client; the tenant extension lives in [[PKG-data-access]] |
| 19.4 | [[ADR-workflow-engine]] | Approved | Temporal, state machines and BullMQ each have a defined scenario |
| 19.5 | [[ADR-container-orchestration]] | Approved | ECS per region, Azure Container Apps where Azure is required |
| 19.6 | [[ADR-temporal]] | Approved | Self-hosted Temporal per region; workflow history never leaves the region |
| 19.7 | [[ADR-queue-technology]] | Approved | BullMQ on Redis; forces a `noeviction` queue Redis |
| 19.8 | [[ADR-aggregator-reporting]] | Approved | Aggregator reports are versioned configuration, not code |
| 19.9 | [[ADR-workflow-interpreter-versioning]] | Proposed | How the generic Temporal interpreter for tenant blueprints is versioned (Auto-Upgrade plus short-lived `patched()`, contract-versioned pure core) |
| 19.10 | [[ADR-expression-and-rules-language]] | Proposed | One sandboxed expression language (CEL profile `expr/1`) for blueprint guards, automation conditions, forms, setting validation and decision tables |
| 19.11 | [[ADR-policy-engine]] | Proposed | Authorisation decisions in TypeScript policies inside `@nomology/authz`, compiled to database filters for lists; Cedar as fallback |
| 19.12 | [[ADR-identity-platform]] | Proposed | Authentication built on vetted libraries in our regional stacks, SAML via self-hosted Ory Polis per region; Keycloak broker as fallback |

**Decisions still to be recorded** (proposed new records; owners to be assigned by the ARB)

| Proposed record | Blocks | Raised in |
|---|---|---|
| Temporal visibility store (Postgres or OpenSearch) | [[INF-temporal]], Phase 3 | [[WF-separation-of-concerns-temporal]] |
| Redis topology: separate queue and cache instances | [[INF-redis]], Phase 2 | [[ADR-queue-technology]] |
| Connection pooler per cloud (PgBouncer, built-in Azure PgBouncer, RDS Proxy) | [[INF-pgbouncer]], Phase 1 | [[INF-pgbouncer]] |
| IaC tool (Terraform or Pulumi) | [[INF-cloud-and-iac]], Phase 0 | [[INF-cloud-and-iac]] |
| AI model providers per region and gateway form (library or service) | [[AI-ai-gateway]], AI phase | [[AI-ai-gateway]] |
| Vector store (pgvector in regional Postgres or a separate store) | [[AI-rag]], AI phase | [[AI-rag]] |
| Search engine per region | [[PKG-search]], Phase 3 | [[PKG-search]] |

<!-- section:map -->
## Capability map

Each child is one Decision record. Gaps are the "still to be recorded" list in Key decisions. There are no overlapping records today; [[ADR-workflow-engine]] (which mechanism) and [[ADR-temporal]] (where Temporal runs) are deliberately separate, as are [[ADR-next-js-hosting]] (what the web tier is) and [[ADR-container-orchestration]] (what runs containers).

Note: [[ADR-reporting-formats-for-msme-and]] carries an `ADR-` identifier but is a regulatory reporting node under [[RPT-aggregators]], not a decision record.

<!-- section:phasing -->
## Phasing

| Phase ([[PLAN]]) | Decisions that must be Approved before the phase starts |
|---|---|
| 0 Foundations | IaC tool; container orchestration (done); Next.js hosting (done) |
| 1 Core platform and residency | Tenant isolation (done); ORM (done); pooler per cloud; identity platform ([[ADR-identity-platform]]); policy engine ([[ADR-policy-engine]]) |
| 2 Shared services | Redis topology; queue technology (done) |
| 3 First domain slice | Workflow engine (done); Temporal hosting (done); interpreter versioning ([[ADR-workflow-interpreter-versioning]]); expression and rules language ([[ADR-expression-and-rules-language]]); visibility store; search engine |
| AI capabilities | AI providers per region and gateway form; vector store |
| Reporting | Aggregator reporting (done) |

Exit rule at each phase gate: no node in the phase may be Approved while a decision it links to is still Proposed.

<!-- section:risks -->
## Risks and open questions

- [ ] Assign an ARB chair deputy and named reviewers for security, data, infrastructure and AI so records are not blocked on one person.
- [ ] Record deciders, consulted and informed groups and approval dates for the eight approved records; today only the decision line exists.
- [ ] Agree the numeric revisit triggers proposed in each record (they are proposals, not agreed thresholds).
- [ ] Decide whether the ID `ADR-reporting-formats-for-msme-and` should be renamed to avoid confusion with decision records (IDs are permanent, so this may need an alias rather than a rename).
- [ ] Risk: approved records written after the fact may not reflect alternatives that were really considered; reviewers should confirm the options sections.
- [ ] Set a review cadence: every record's revisit triggers checked at each phase boundary.

<!-- checks -->
## Template checks

<!-- check:ownership -->
### Ownership and governance

Accountable owner: the ARB chair (AI platform and governance lead). Deputy and specialist reviewers (security, data, infrastructure, AI) are still to be named (see Risks). Change route: anyone proposes a record through a pull request or workspace node in Proposed status; the ARB approves at its fortnightly meeting (proposed cadence) or asynchronously with two named approvers. The area is reviewed at each phase boundary of [[PLAN]].

<!-- check:principles -->
### Principles and enforcement

Each principle in the table names its enforcement point. P2 (no rewriting) and P4 (confirmation required) are enforced by workspace status rules and ARB refusal. Exceptions to an Approved record are recorded as a Proposed superseding record or a time-limited exception note on the record, approved by the ARB with an expiry date.

<!-- check:decisions -->
### Decisions linked

All eight Approved records are listed with their effect. Nine decisions still to be recorded are listed with the nodes and phases they block, the place they were raised, and owners to be assigned by the ARB. Each Approved record has measurable revisit triggers in its own "When to revisit" section.

<!-- check:regions -->
### Tenancy and residency

Most records are explicitly per-region (hosting, orchestration, Temporal, queues, tenant isolation within a regional database). Every record states its residency effect. Azure variation is contained in [[ADR-container-orchestration]] and the infrastructure nodes it governs.

<!-- check:phase -->
### Phasing

The phasing table lists which decisions must be Approved before each [[PLAN]] phase starts, with a gate rule: no node is Approved while a linked decision is Proposed. The IaC tool and pooler decisions are needed earliest (Phase 0 and 1).

<!-- end -->
