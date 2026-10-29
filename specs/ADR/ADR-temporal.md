---
id: "ADR-temporal"
title: "Temporal hosting"
parent: "ADR"
order: 6
type: "decision"
template: "adr"
status: "approved"
owner: null
indicative: false
summary: "Self-hosted, per region"
links: []
rev: 3
syncHash: "fe7b9ea35a3e9eb0"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 19.6 Temporal hosting

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Self-hosted, per region

<!-- section:context -->
## Context and problem

**Question:** where does the Temporal service that runs our durable workflows ([[ADR-workflow-engine]]) live: Temporal Cloud or our own clusters, and one global cluster or one per region?

Affected parts: [[INF-temporal]], [[WF-separation-of-concerns-temporal]] (layer 4, runtime), [[WF-long-running-pipelines]], [[INF-backup-and-disaster-recovery]], [[SEC-business-continuity]].

Workflow history contains activity inputs and outputs: case identifiers, party names, deadlines, document references and, for AI pipelines, prompts and outputs. Even with payload encryption, history metadata (workflow IDs, search attributes such as `tenantId` and `caseId`, timers) is stored by the Temporal service.

<!-- section:drivers -->
## Decision drivers

- **D1 Residency:** workflow history and visibility data must stay in the tenant's home region.
- **D2 Availability** of a region's case processes must not depend on another region.
- **D3 Operating effort** for a small team.
- **D4 Cost** at our expected workflow volumes.
- **D5 Azure support** for clients that require it.
- **D6 Confidentiality:** payloads encrypted with keys we hold.

<!-- section:decision -->
## Decision

**Self-hosted, per region.**

- One Temporal cluster per region and per production environment, running alongside the app containers ([[ADR-container-orchestration]]), with Postgres persistence in the same region ([[INF-temporal]]).
- Namespaces per environment and region (for example `prod-in`, `prod-sg`, `prod-us`); tenants are carried in context and search attributes, not in per-tenant namespaces ([[WF-separation-of-concerns-temporal]]).
- Payloads are encrypted by a Payload Codec with keys from the regional KMS; the Codec Server runs in the region and decrypts only for authorised operators.
- No cross-region replication of workflow history. Regional disaster recovery restores the persistence store inside the same country or jurisdiction ([[INF-backup-and-disaster-recovery]]).

Justification: per-region clusters meet D1 and D2 without depending on a vendor's regional footprint; self-hosting meets D5 on Azure; regional keys meet D6. D3 is the cost we accept.

<!-- section:consequences -->
## Consequences

**Easier:** residency story is simple; no extra sub-processor for workflow data; cost is infrastructure only.

**Harder:**

- We own upgrades, scaling and monitoring of Frontend, History, Matching and Worker services per region. Temporal's own checklist warns that the history shard count is fixed when the cluster is created and that upgrades must not skip minor versions [R1].
- Self-hosted Temporal has no built-in RBAC or audit logging for operators [R1]; we must restrict Web UI and CLI access at the network and identity layer and log operator actions ourselves ([[PKG-audit-trail]]).
- Three or more clusters to patch and test; DR drills per region.
- The visibility store choice (Postgres or OpenSearch) remains open ([[WF-separation-of-concerns-temporal]]).

<!-- section:confirmation -->
## Confirmation

- IaC review: each region's Temporal persistence and visibility stores are in that region's account / subscription; a policy check blocks cross-region replication settings.
- A worker start-up check refuses to connect to a namespace whose region suffix differs from the worker's `REGION`.
- Monthly operational review of Temporal service metrics (`service_requests`, `service_errors`, `persistence_latency`) per region in [[OBS-performance]].
- DR restore drill of Temporal persistence per region on the schedule in [[INF-backup-and-disaster-recovery]].

<!-- section:options -->
## Options considered

| Option | D1 residency | D3 effort | D5 Azure | Verdict |
|---|---|---|---|---|
| **Self-hosted, per region** | Full control | High | Yes | **Chosen** |
| Temporal Cloud, regional namespaces | Depends on vendor region availability in India, Singapore and US and on contract terms; metadata held by a sub-processor | Low | Not hosted on Azure by us | Rejected at decision time; strongest candidate on revisit |
| Self-hosted, one global cluster | Fails D1 | Medium | Yes | Rejected |

<!-- section:revisit -->
## When to revisit

- Temporal Cloud (or another managed option) offers namespaces in all our regions with contractual residency, acceptable sub-processor terms and pricing within a proposed threshold of our self-hosting cost.
- Self-hosting incidents or upgrade effort exceed a proposed two engineer-weeks per quarter across regions.
- A client requires a dedicated Temporal cluster.

<!-- section:notes -->
## More information

**Open questions**

- [ ] Visibility store per region: Postgres or OpenSearch (carried from [[WF-separation-of-concerns-temporal]]).
- [ ] History shard count per region (fixed at creation), based on projected workflow volume.
- [ ] Separate Postgres instance for Temporal persistence or a separate database on the regional instance?
- [ ] Who may use Temporal Web UI and the Codec Server in production, and through what break-glass process ([[SEC-access-reviews]])?

<!-- checks -->
## Template checks

<!-- check:significance -->
### Significance

Significant: it decides where workflow history for every case lives, adds or removes a sub-processor, and is expensive to change once multi-year case workflows are running. It covers hosting only; when to use Temporal is [[ADR-workflow-engine]].

<!-- check:compliance -->
### Regulatory, residency and tenancy fit

Residency: workflow history, visibility and codec keys stay in-region. Sub-processors: none added. Audit: self-hosted Temporal lacks operator audit logging, so operator access is logged by our identity and network layers. Encryption: payload codec with regional KMS keys ([[INF-secrets-and-keys]]). Reviewer and date to be recorded.

<!-- check:consequences -->
### Consequences and costs

Downsides: upgrade and scaling ownership, fixed shard count, no built-in operator RBAC or audit, per-region DR drills. Follow-ups tracked in [[INF-temporal]].

<!-- check:reversibility -->
### Reversibility and revisit triggers

Moving to a managed service later means running new workflows on the new service while old ones drain on the self-hosted cluster (Temporal does not migrate running history between clusters in a simple way). With multi-month cases, the drain could take a long time, so the cost rises with time. Keeping workflow IDs, search attributes and codec independent of the hosting choice keeps that path open.

<!-- check:confirmation -->
### Confirmation

Policy check blocking cross-region replication, worker start-up namespace-region check, monthly metrics review, and scheduled restore drills per region.

<!-- check:linked -->
### Linked and lifecycle

Governs [[INF-temporal]] and runtime layer of [[WF-separation-of-concerns-temporal]]. Related: [[ADR-workflow-engine]], [[ADR-container-orchestration]]. Status: Approved.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Shard count is set at build time and cannot be adjusted later; monitor service_requests/errors/latency and persistence_requests/errors/latency; upgrade sequentially without skipping minor versions; self-hosted Temporal has no RBAC or audit logging out of the box.",
    "id": "R1",
    "kind": "vendor",
    "title": "Temporal self-hosted production checklist",
    "url": "https://docs.temporal.io/self-hosted-guide/production-checklist",
    "vendor": "Temporal Technologies"
  }
]
```

<!-- end -->
