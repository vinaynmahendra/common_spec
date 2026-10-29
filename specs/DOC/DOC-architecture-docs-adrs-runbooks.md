---
id: "DOC-architecture-docs-adrs-runbooks"
title: "Architecture docs and runbooks"
parent: "DOC"
order: 1
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: "arc42-style architecture overview, C4 diagrams and operational runbooks; the ADR process is owned by 1.5 Governance and the Decisions area (19)"
links: []
rev: 3
syncHash: "57ed31eda54feeb8"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 17.1 Architecture docs and runbooks

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> arc42-style architecture overview, C4 diagrams and operational runbooks; the ADR process is owned by 1.5 Governance and the Decisions area (19)

<!-- section:purpose -->
## Purpose and scope

Defines how the platform's architecture is described (an arc42-structured overview with C4 diagrams) and how operational runbooks are written, stored, linked and tested. Decision records are governed by [[FND-governance]] and stored as nodes under [[ADR]]; this node only says how architecture docs link to them.

<!-- section:rules -->
## Rules

**Architecture overview**
- **ARCH-1** `docs/architecture/` holds one arc42-structured overview [R1] with these sections filled for the platform: introduction and goals, constraints (residency, regulations), context and scope, solution strategy, building block view, runtime view, deployment view (per region and Azure), cross-cutting concepts (tenancy, audit, i18n, accessibility), decisions (links to ADR nodes), quality requirements, risks and glossary (link to [[I18N-platform-glossary-and]]).
- **ARCH-2** Diagrams follow the C4 model [R2]: one system context diagram, one container diagram per region type (AWS, Azure), and component diagrams for `apps/web`, `apps/worker-temporal` and the AI gateway. Diagrams are text (Structurizr DSL or Mermaid) in the repo and rendered in CI.
- **ARCH-3** The overview links to spec nodes rather than repeating them; where it summarises a node, it names the node ID.
- **ARCH-4** The architecture overview is reviewed at every phase boundary of [[PLAN]], and any ADR that is accepted updates the relevant arc42 section in the same week.

**Runbooks**
- **ARCH-5** Every alert defined in [[OBS-alerting]] has a `runbook_url` pointing to a runbook in `docs/runbooks/`. CI fails if an alert rule lacks one.
- **ARCH-6** Runbooks use the template: Summary, Impact (which tenants, regions, personas), Detection (alert and dashboards), Diagnosis steps (exact commands and queries), Mitigation, Rollback, Escalation (on-call rota, incident lead, information security owner if data may be affected), Communication (status page, tenant admins), Verification, Last tested.
- **ARCH-7** Runbook commands that touch production name the role used and the just-in-time access step; no runbook asks the operator to connect as the migration role or to disable RLS.
- **ARCH-8** Runbooks for high-severity scenarios (region outage, database failover, Temporal cluster loss, suspected cross-tenant exposure, secrets compromise, aggregator submission failure) are exercised at least twice a year in game days, and the "Last tested" field is updated.
- **ARCH-9** Runbooks contain no secrets, no real tenant names and no case data.

<!-- section:rationale -->
## Rationale

- arc42 gives a known structure that auditors and new engineers can navigate; C4 keeps diagrams at consistent levels.
- **ARCH-5, ARCH-8** An untested runbook found during an incident is often wrong; linking alerts to runbooks and testing them makes them part of operations rather than shelf documents.
- **ARCH-7** Incidents are when people take shortcuts; runbooks must not normalise bypassing tenant isolation.

<!-- section:tooling -->
## Tooling and configuration

- MDX docs site built from `docs/` (internal, SSO).
- Structurizr DSL (`docs/architecture/workspace.dsl`) or Mermaid for diagrams, rendered in CI.
- Alert-rule linter checking `runbook_url` annotations.
- `turbo gen runbook` template.

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| ARCH-1, ARCH-2 | Docs build fails on missing required sections or broken diagram sources |
| ARCH-3 | Link checker validates node IDs and repo links |
| ARCH-4 | Phase-boundary checklist item in [[PLAN]] |
| ARCH-5 | Alert-rule lint (required) |
| ARCH-6 | Front-matter schema for runbooks |
| ARCH-8 | Front-matter `last_tested`; weekly report of high-severity runbooks older than 6 months |
| ARCH-9 | gitleaks on `docs/`; review |

<!-- section:examples -->
## Examples

Good runbook title: "Temporal schedule-to-start latency high in prod-in", diagnosis step `tctl` / `temporal` CLI commands against namespace `prod-in`, mitigation "scale `worker-temporal-cases` service", escalation to platform on-call.

Bad: "Fix DB issues — log in as postgres and run the fix script".

<!-- section:exceptions -->
## Exceptions

New alerts may ship with a stub runbook (Summary, Escalation) for at most 10 working days, tracked by ticket.

<!-- section:questions -->
## Open questions

- [ ] Structurizr DSL or Mermaid as the diagram standard?
- [ ] Where do client-specific Azure deployment diagrams live, given contract confidentiality?
- [ ] Who runs game days, and are clients invited to observe DR exercises?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Alert-to-runbook linkage, front-matter and docs builds are CI-enforced; phase reviews and game days are checklist and calendar items.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

ARCH-7 and ARCH-9 keep runbooks from bypassing RLS or exposing secrets and tenant data.

<!-- check:compliance -->
### Compliance evidence

Runbooks are the documented operating procedures expected by ISO/IEC 27001:2022, and game-day records support business continuity evidence in [[SEC-business-continuity]].

<!-- check:measurement -->
### Adoption measurement

Alerts with runbooks (target 100%), high-severity runbooks tested in the last 6 months, architecture overview last-reviewed date.

<!-- check:ownership -->
### Ownership and change

Owner: engineering excellence lead for the overview; each runbook's owner is the team owning the alert.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "A template of twelve sections for communicating and documenting software architecture.",
    "id": "R1",
    "kind": "web",
    "publisher": "arc42",
    "title": "arc42 documentation",
    "url": "https://docs.arc42.org/home/"
  },
  {
    "excerpt": "A system context diagram shows the software system in scope and its relationships with users and other systems.",
    "id": "R2",
    "kind": "web",
    "publisher": "c4model.com",
    "title": "C4 model: System context diagram",
    "url": "https://c4model.com/diagrams/system-context"
  }
]
```

<!-- end -->
