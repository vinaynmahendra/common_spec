---
id: "SEC-business-continuity"
title: "Business continuity"
parent: "SEC"
order: 8
type: "capability"
template: "control"
status: "draft"
owner: null
indicative: false
summary: "Continuity plan per region and entity, including loss of a region where data cannot leave it, people and supplier dependencies, and exercise schedule"
links: []
rev: 2
syncHash: "764847d585cf0648"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 13.8 Business continuity

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Continuity plan per region and entity, including loss of a region where data cannot leave it, people and supplier dependencies, and exercise schedule

<!-- section:objective -->
## Control objective

Institutions can keep running their cases, and legally significant deadlines (hearings, filing windows, award service) are protected, through the loss of a cloud availability zone, a whole region, a key supplier or key people — without moving a tenant's data out of its home country.

<!-- section:mapping -->
## Framework mapping

| Framework | Clause |
|---|---|
| ISO/IEC 27001:2022 | A.5.29 Information security during disruption; A.5.30 ICT readiness for business continuity; A.8.13 Information backup; A.8.14 Redundancy of information processing facilities |
| SOC 2 TSC | A1.2 (environmental protections, backup and recovery infrastructure), A1.3 (recovery plan testing), CC9.1 (business disruption risk) |
| ISO 22301:2019 | Reference model for BIA, strategies and exercising [R1] (certification not planned) |

<!-- section:description -->
## Control description

**Business impact analysis** (proposed figures, to be confirmed with operations and clients)

| Service | Impact if down | Max tolerable downtime | RTO | RPO |
|---|---|---|---|---|
| Case access and filing (all personas) | Missed filing deadlines, disputes about timeliness | 24 h | 4 h | 15 min |
| Hearing room and video | Hearings lost or adjourned | 2 h during scheduled hearings | 1 h (fallback to provider's direct link) | n/a |
| Notices and service ([[DOM-service-of-notices-and-proof]]) | Service deadlines missed | 24 h | 8 h | 0 (no lost notices; queues durable) |
| Workflows and deadline timers (Temporal) | Reminders and escalations late | 24 h | 4 h | 15 min |
| Public / aggregator API (SEBI ODR intake) | Matters not registered on time | 24 h | 8 h | 15 min |
| Billing and invoicing | Cash flow delay | 5 days | 48 h | 1 h |
| Reporting | Late reports | 5 days | 72 h | 24 h |

**Scenarios and strategies**

| Scenario | Strategy |
|---|---|
| Availability zone loss | Multi-AZ Postgres, Redis, Temporal and containers in each region; automatic failover ([[INF-database]], [[INF-orchestration]]) |
| Region loss (cloud region down for days) | Restore in a second in-country region where one exists (for example a second Indian region), from cross-region backups that stay in-country; where no second in-country region exists (assumption: Singapore), restore in the same region when available, and keep a read-only offline export option for urgent matters subject to legal advice. Residency is never broken without the tenant's written agreement ([[MT-data-residency-2]]). |
| Loss of Temporal cluster state | Domain tables are the source of truth for deadlines; a recovery job recreates workflows from domain state ([[INF-temporal]]) |
| Supplier failure (messaging, video, e-sign, KYC) | Second provider per critical category per region where feasible; manual fallback procedures (for example email service with delivery evidence when SMS fails) |
| Ransomware / destructive attack | Immutable backups with separate credentials; restore drills; incident process ([[SEC-security-incident-response-and]]) |
| Loss of key people / Bangalore office | Documented runbooks ([[DOC-architecture-docs-adrs-runbooks]]), cross-trained on-call, remote work capability, no single person holding sole access to production or keys |
| Global component failure (directory, DNS, CI) | Regional directory replicas; DNS with long TTL and secondary provider; manual deploy procedure documented |

**Deadline protection.** If the platform is unavailable for a period that affects deadlines, the tenant secretariat receives an outage certificate (start, end, affected services) generated from monitoring data, so tribunals and institutions can apply their rules on extensions. Assumption: institutional rules allow such extensions; to be confirmed per tenant.

**Plans.** One continuity plan per region (India, Singapore, US, Azure deployments) and per entity (NTPL, TAPL, US entity) covering activation criteria, roles, communication templates for tenants, and recovery runbooks.

<!-- section:owner -->
## Owner and frequency

Owner: CTO. Operator: platform engineering lead (technical recovery), ISMS lead (plan maintenance and exercises). Backup: DevOps lead. Frequency: BIA annually; plans reviewed annually and after major change; restore drill per region quarterly; region-loss exercise annually; tabletop for people / supplier scenarios annually.

<!-- section:evidence -->
## Evidence

- BIA and plans (versioned, approved by the CTO).
- Restore drill records per region: date, backup restored, time to restore, data verified, issues (3 years).
- Exercise reports with findings and actions.
- Backup job success records ([[INF-backup-and-disaster-recovery]]).
- Outage certificates issued to tenants.

<!-- section:test -->
## Test procedure

Auditor inspects the 4 most recent quarterly restore drills per region (achieved RTO / RPO versus target), the annual exercise report and action closure, and confirms plans were reviewed within 12 months.

<!-- section:implementation -->
## Implementation in the platform

[[INF-backup-and-disaster-recovery]] (RPO / RTO, immutable backups, restore drills), [[INF-database]] (multi-AZ, replicas), [[INF-temporal]] (cluster recovery), [[OBS-uptime-synthetic-monitoring]] (status page and outage evidence), [[MT-data-residency-2]] (in-country recovery rule).

<!-- section:exceptions -->
## Exceptions

A region whose recovery strategy cannot meet the RTO (for example no second in-country region) is recorded as an accepted risk with the CTO's approval and disclosed to tenants in that region on request.

<!-- section:metrics -->
## Monitoring and KPIs

- Restore drills done per region per quarter (target 1) and achieved RTO / RPO.
- Open exercise actions past due (target 0).
- Monthly availability per region versus SLO.

<!-- section:questions -->
## Open questions

- [ ] Confirm RTO / RPO targets with operations and against client SLAs.
- [ ] Which regions have a second in-country cloud region available, and is a second Indian region used for DR? Owner: DevOps.
- [ ] Do institutional clients accept read-only offline exports during prolonged region loss, and under what controls?
- [ ] Should outage certificates be a product feature in Phase 7?

<!-- checks -->
## Template checks

<!-- check:scope -->
### Scope and population

All regional stacks (India, Singapore, US, Azure deployments), global components, the three entities, key suppliers and key staff roles. The population comes from the service catalogue and vendor register.

<!-- check:automation -->
### Automation and continuous monitoring

Backups, multi-AZ failover and backup success monitoring are automated; restore drills are scripted but triggered by people; exercises and BIA are manual.

<!-- check:deficiency -->
### Failures and remediation

A failed restore drill or missed RTO is a nonconformity with corrective action and a repeat drill within 30 days; if it reveals that backups are unusable, it is treated as a SEV2 incident.

<!-- check:assurance -->
### Independent assurance

SOC 2 auditor tests A1.2 / A1.3; cloud providers' resilience is inherited and reviewed through their reports; annual exercise reviewed by the ISMS lead independently of the team that ran it.

<!-- check:commitments -->
### Legal and client commitments

Client SLAs (availability, RTO) and residency clauses both constrain this control: recovery must not move data out of country. Changing DR regions requires a residency check and possibly client consent.

<!-- citations -->
## Citations

```json
[
  {
    "body": "ISO",
    "excerpt": "Requirements for business impact analysis, continuity strategies, plans and exercising.",
    "id": "R1",
    "ident": "ISO 22301",
    "kind": "standard",
    "title": "Security and resilience — Business continuity management systems — Requirements",
    "url": "https://www.iso.org/standard/75106.html",
    "version": "2019"
  }
]
```

<!-- end -->
