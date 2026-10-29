---
id: "INF-backup-and-disaster-recovery"
title: "Backup and disaster recovery"
parent: "INF"
order: 10
type: "capability"
template: "infra"
status: "draft"
owner: null
indicative: false
summary: "Backup policies, immutable in-region vaults, RPO / RTO per component and per failure, restore and failover drills, and the region-loss plan per residency region"
links: []
rev: 2
syncHash: "caf35c9a3a010adf"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 14.10 Backup and disaster recovery

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Backup policies, immutable in-region vaults, RPO / RTO per component and per failure, restore and failover drills, and the region-loss plan per residency region

<!-- section:purpose -->
## Purpose and responsibilities

Defines what is backed up, where copies live, how fast each component can be recovered, and how that is proven. Each component node states its own failover behaviour; this node owns the **platform-level targets**, the backup vaults and the drill programme, and is the infrastructure evidence for [[SEC-business-continuity]] and ISO 27001 backup and ICT continuity controls [R1].

Constraint that shapes everything: tenant data must stay in its pinned region ([[MT-data-residency-2]]). Backups and DR copies therefore stay in-region or in a second region **inside the same country**, never abroad, unless a documented exception exists.

<!-- section:topology -->
## Topology per region

| Region | Primary | Backup vault (separate account, same region) | In-country DR region | DR status |
|---|---|---|---|---|
| India | ap-south-1 Mumbai | `nomo-backup-in`, ap-south-1 | ap-south-2 Hyderabad (copy of backups + Postgres cross-region replica) | Proposed, needs approval |
| Singapore | ap-southeast-1 | `nomo-backup-sg`, ap-southeast-1 | **None on AWS** (one AWS region in Singapore) | Open decision |
| US | us-east-1 | `nomo-backup-us`, us-east-1 | us-west-2 Oregon | Proposed |
| Azure regions | e.g. Central India | Recovery Services / Backup vault, immutable | Paired region in the same country where one exists (e.g. South India) | Per client |

Options for Singapore region loss, for decision: (a) multi-AZ only, accept that full-region loss means waiting for AWS recovery, and say so in contracts; (b) warm standby on Azure Southeast Asia (also in Singapore) with backups restored cross-cloud; (c) a lawful copy outside Singapore under the PDPA transfer limitation obligation [R2] for clients who agree.

<!-- section:sizing -->
## Sizing and scaling

| Data | Backup method | Retention (proposed) |
|---|---|---|
| Postgres (application) | RDS automated backups with PITR | 35 days |
| | Daily snapshot copied to backup vault | 35 daily, 12 monthly |
| Postgres (Temporal) | Automated backups with PITR | 14 days |
| Object storage (documents, bundles, recordings) | S3 versioning + replication to vault bucket with Object Lock (compliance mode) | Non-current versions 35 days; locked copies per retention schedule |
| Redis | Daily snapshot (queue); none (cache) | 7 days |
| Terraform state, configuration | Versioned buckets, daily copy to vault | 90 days |
| Audit and security logs | Write-once bucket in log archive ([[OBS-security-events]]) | ≥ 1 year; India system logs ≥ 180 days in India [R3] |

Backup retention must not keep personal data past its deletion date longer than the backup cycle: deletions and legal holds are governed by [[PKG-data-retention-legal-hold-and]]; backups age out within 12 months and are never restored to production without re-applying deletions recorded since the backup (the "deletion replay" step below).

<!-- section:config -->
## Configuration baseline

- AWS Backup plans defined in the `backup` module; vaults in the backup account with **Vault Lock in compliance mode** so nobody, including account root, can delete recovery points before expiry.
- Cross-account copy uses the backup account's KMS key ([[INF-secrets-and-keys]]).
- Backup frameworks / audit reports enabled to produce evidence of compliance with the plan.
- S3 document buckets: versioning, Object Lock on the vault copy, replication within the region to the backup account; replication to the in-country DR region only where approved.
- Cross-region copy rules are permitted by policy-as-code only for the pairs India → Hyderabad and US-East → US-West.

<!-- section:resilience -->
## High availability and DR

**Targets per failure (proposed, platform level)**

| Failure | RPO | RTO | Mechanism |
|---|---|---|---|
| Task / instance failure | 0 | < 5 min | Multi-AZ, ECS replacement |
| Availability-zone loss | 0 | < 15 min | 3-AZ design across all components |
| Bad deploy / bad migration | 5 min | 1–4 h | Rollback; PITR to a new instance and targeted repair |
| Ransomware or malicious admin | 24 h | 8–24 h | Restore from locked vault in the backup account |
| Region loss — India, US (with in-country DR) | 15 min | 8 h | Rebuild stack in DR region from IaC; promote cross-region replica or restore backups |
| Region loss — Singapore | Depends on decision | Depends on decision | See topology options |
| Loss of the production cloud account | 24 h | 24–48 h | Backup account restores into a newly created account |

Client-facing implications: hearing days and filing deadlines. A region outage longer than the RTO must trigger the deadline-extension process owned by the tenant (institution rules), which the platform supports by recording the outage window — see questions.

**Restore order** for a region: network → keys → Postgres (app) → Postgres (Temporal) → Redis (empty) → object storage → apps → Temporal reconciliation ([[INF-temporal#resilience]]) → outbox re-enqueue ([[INF-redis#resilience]]) → deletion replay → smoke tests → DNS switch.

<!-- section:security -->
## Security

- Backup account is separate, with its own SSO permission sets; production admins have no rights in it.
- Vault Lock (compliance mode) and S3 Object Lock make recovery points immutable.
- Restores require two people (requester and approver) and are logged; restored data stays in the same region.
- Restore tests use isolated VPCs with no internet egress; test restores are deleted within 7 days.

<!-- section:operations -->
## Runbook

**Drill programme**

| Drill | Frequency | Environment | Pass criteria |
|---|---|---|---|
| Postgres Multi-AZ forced failover | Quarterly | Staging and production (maintenance window) | Error burst < 2 min; retries succeed |
| Redis failover | Quarterly | Staging and production | Workers reconnect; no lost outbox-backed job |
| Postgres PITR to new instance + smoke test | Quarterly | Staging; yearly production restore to isolated account | Row counts, checksums on sampled tables, app smoke test |
| Object storage restore of a deleted document | Quarterly | Production (test tenant) | Version restored within 1 h |
| Full region rebuild from IaC + backups | Yearly | Staging region (and DR region for India / US once approved) | Within region-loss RTO |
| Tabletop: region loss and client communication | Yearly | — | Runbook updated |

Each drill produces a record (date, duration vs RTO, issues, actions) stored as ISO 27001 / SOC 2 evidence ([[SEC-isms-controls]]).

**Deletion replay**: after any restore, re-run deletion and anonymisation jobs for every deletion recorded after the restore point (from the deletion log kept by [[PKG-data-retention-legal-hold-and]]) before the data is used.

<!-- section:observability -->
## Monitoring and alerts

- Backup job failures → ticket; two consecutive failures for Postgres or documents → page.
- Missing recovery point (no snapshot in 26 h) → page.
- Vault compliance report deviations → security ticket.
- Drill overdue (no successful drill record in 100 days for quarterly drills) → ticket to the Infrastructure owner.

<!-- section:cost -->
## Cost

Drivers: snapshot storage (incremental), vault copies, S3 replica storage and replication requests, cross-region transfer to DR regions, and warm resources in DR regions (none by default; pilot-light only). The Singapore option (b) adds a standing Azure footprint.

<!-- section:readiness -->
## Production readiness

| Item | Status |
|---|---|
| Backup account and locked vaults per region | Not started |
| Backup plans for all stateful components | Not started |
| First PITR restore drill in staging | Not started |
| Deletion replay procedure tested | Not started |
| Region-loss decision for Singapore | Open |
| Client communication template for region outage | Not started |

<!-- section:questions -->
## Open questions

- [ ] Approve in-country DR regions: India → ap-south-2 Hyderabad, US → us-west-2. Any client or legal reason against?
- [ ] Choose the Singapore region-loss option (multi-AZ only, Azure Southeast Asia standby, or lawful copy abroad) and confirm with legal under PDPA.
- [ ] Are the proposed region-loss targets (RPO 15 min / RTO 8 h) acceptable to institutions with hearing schedules, and what do client contracts promise today?
- [ ] Backup retention vs deletion obligations under DPDP and GDPR: is 12 months of monthly snapshots acceptable with deletion replay? (To be confirmed by legal / DPO.)
- [ ] Who declares a region disaster and approves failover?

<!-- checks -->
## Template checks

<!-- check:security -->
### Security

Separate backup account with its own permissions, immutable vaults, its own KMS key, two-person restore approval and isolated restore-test networks.

<!-- check:residency -->
### Data residency

All backups stay in the region, in a separate account. Cross-region copies are allowed by policy only for in-country pairs (India → Hyderabad, US-East → US-West). Any copy abroad (Singapore option c) needs a legal basis under the PDPA transfer limitation obligation [R2] and client agreement. India system logs are kept in India for at least 180 days [R3].

<!-- check:dr -->
### Resilience and recovery

Targets are set per failure type, from task failure (RPO 0 / RTO 5 min) to region loss (RPO 15 min / RTO 8 h for India and US with in-country DR) and loss of the cloud account (restore from a separate, locked backup account). Backups are immutable through Vault Lock in compliance mode and S3 Object Lock. Drills run quarterly for failover and PITR and yearly for a full region rebuild; each produces a stored record. The Singapore region-loss limit is an explicit open decision that must be explained to clients.

<!-- check:observability -->
### Monitoring and alerting

Backup failures, missing recovery points and overdue drills all alert a named owner, so a silent backup gap is detected within a day.

<!-- check:lifecycle -->
### Operations and lifecycle

The restore order, deletion replay step and drill programme are written down; drills keep the runbook current and train new on-call engineers.

<!-- check:cost -->
### Cost

DR regions run as pilot light (data copies only, no standing compute) to keep cost low; the trade-off is the 8-hour RTO for region loss.

<!-- citations -->
## Citations

```json
[
  {
    "body": "ISO/IEC",
    "excerpt": "Annex A includes controls on logging (8.15), monitoring activities (8.16), clock synchronisation (8.17), backup (8.13) and ICT readiness for business continuity (5.30).",
    "id": "R1",
    "ident": "ISO/IEC 27001",
    "kind": "standard",
    "title": "Information security management systems — Requirements",
    "url": "https://www.iso.org/standard/27001",
    "version": "2022"
  },
  {
    "excerpt": "An organisation transferring personal data outside Singapore must ensure the recipient is bound to a comparable standard of protection.",
    "id": "R2",
    "issuer": "Personal Data Protection Commission, Singapore",
    "jurisdiction": "Singapore",
    "kind": "regulation",
    "ref": "Advisory Guidelines on Key Concepts in the PDPA, Chapter 19",
    "title": "The Transfer Limitation Obligation",
    "url": "https://www.pdpc.gov.sg/-/media/files/pdpc/pdf-files/advisory-guidelines/the-transfer-limitation-obligation---ch-19-(270717).pdf"
  },
  {
    "excerpt": "Reportable cyber incidents to be reported to CERT-In within 6 hours of noticing; logs of ICT systems to be maintained securely for a rolling period of 180 days within Indian jurisdiction; clocks to be synchronised to NTP servers of NIC/NPL or traceable sources.",
    "id": "R3",
    "issued": "2022-04-28",
    "issuer": "CERT-In, Ministry of Electronics and IT, Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Directions under sub-section (6) of section 70B of the IT Act, 2000 (No. 20(3)/2022-CERT-In)",
    "title": "CERT-In Directions relating to information security practices, procedure, prevention, response and reporting of cyber incidents",
    "url": "https://www.cert-in.org.in/PDF/CERT-In_Directions_70B_28.04.2022.pdf"
  }
]
```

<!-- end -->
