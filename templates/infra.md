# Template: Infrastructure component (`infra`)

Generated from `infra.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies a piece of runtime infrastructure so it can be built from code, operated safely in every region, and recovered when it fails.

**Depth:** 3–8 pages. Topology, sizing, HA/DR targets and the runbook are mandatory for Approved. Use the Well-Architected pillars as the review lens and a production readiness review as the go-live gate. Region-specific differences go in a table, not separate nodes, unless they diverge materially.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose and responsibilities (level 1)

What the component does for the platform and which services depend on it.

Illustrative example (not a requirement):

> Redis per region serves BullMQ queues (notifications, scans, indexing) and the application cache. Loss of Redis delays background jobs and slows pages; it must never lose queued jobs that represent legal notifications.

### `topology` Topology per region (level 1)

Diagram and table of deployment per region and environment.

Illustrative example (not a requirement):

> | Region | Environment | Deployment |
> |---|---|---|
> | India (Mumbai) | prod | Managed Redis, primary + replica across 2 AZs |
> | Singapore | prod | Same |
> | US | prod | Same |
> | India | staging | Single node |

### `sizing` Sizing and scaling (level 1)

Starting size, growth assumptions, scaling triggers.

Illustrative example (not a requirement):

> Start: 2 vCPU / 6 GB per region. Scale up at 70% memory or > 5k ops/s sustained. Queue and cache use separate logical DBs; split into two clusters if cache evictions affect queues.

### `config` Configuration baseline (level 2)

Key settings and why; where configuration lives (IaC module).

Illustrative example (not a requirement):

> `maxmemory-policy noeviction` on the queue cluster (jobs must not be evicted); AOF persistence every second; TLS required; IaC module `infra/modules/redis` with per-region variables.

### `resilience` High availability and DR (level 1)

Failure modes, RPO / RTO, failover behaviour, backup and restore, drill frequency.

Illustrative example (not a requirement):

> | Failure | Behaviour | RPO | RTO |
> |---|---|---|---|
> | Primary node loss | Automatic failover to replica | ≤ 1 s | < 2 min |
> | Region loss | No cross-region failover (residency); jobs replayed from Postgres outbox | 0 for notifications | Region restore |
> 
> Restore drill every 6 months.

### `security` Security (level 1)

Network placement, access, auth, encryption, secrets.

Illustrative example (not a requirement):

> Private subnets only; reachable from app and worker security groups. AUTH token in secrets manager, rotated quarterly. Encryption at rest with region KMS key.

### `operations` Runbook (level 2)

Routine operations and incident steps, or a link to the runbook node.

Illustrative example (not a requirement):

> - High memory: check queue backlogs first (`bullmq:*:wait` lengths), then cache key growth
> - Failover: verify app reconnects; check worker logs for `ECONNRESET` storms

### `observability` Monitoring and alerts (level 2)

Metrics, dashboards, alert thresholds and routing.

Illustrative example (not a requirement):

> Alerts: memory > 80% (warn), > 90% (page); replication lag > 5 s; any queue wait > 10k jobs.

### `cost` Cost (level 3)

Estimated monthly cost per region and drivers.

Illustrative example (not a requirement):

> ≈ USD 250 / region / month at starting size.

### `readiness` Production readiness (level 2)

Go-live checklist status.

Illustrative example (not a requirement):

> - [x] IaC reviewed
> - [ ] Restore drill passed
> - [ ] Alerts routed to on-call

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Azure Cache for Redis equivalence for clients requiring Azure

## Checks

### `security` Security

**Question:** Is the component reachable only by the services that need it, accessed only with least-privilege identities, and encrypted in transit and at rest with keys we control per region?

- Which subnets and security groups (or Azure network security groups / private endpoints) does it sit in, is it free of any public IP or public endpoint, and which exact sources may connect on which ports?
- Which IAM roles / managed identities can administer it versus use it, and is human admin access through short-lived, MFA-backed sessions with a logged break-glass path rather than standing credentials?
- Is TLS required on every connection (Postgres sslmode=verify-full, Redis TLS, Temporal mTLS between frontend, history and workers), and with which minimum TLS version?
- Is data at rest encrypted with a customer-managed KMS key per region (Postgres storage, snapshots, Redis, S3, Temporal persistence), who can use the key, and is key rotation on?
- How are credentials for the component (DB passwords, Redis ACL users, Temporal certificates) stored and rotated, and how long does a rotation take to reach all services?
- Which hardening baseline applies (CIS Benchmark for the OS or service, Postgres parameters such as password_encryption=scram-sha-256, Redis ACLs with the default user disabled), and how is drift from it detected?
- How are patches and security fixes for the engine version applied, and within what time after a critical CVE?

**Good answer:** A network table (source, destination, port, reason) showing no public exposure, the IAM roles split into admin and runtime with least-privilege policies in the IaC module, and the encryption settings with KMS key ARNs per region. Credentials live in the regional secrets manager with an automatic rotation period stated. Names the hardening baseline and the tool that reports drift, and the patch window for critical vulnerabilities (for example 7 days).

**Red flags:**

- Any public endpoint or 0.0.0.0/0 ingress rule
- Shared admin password or long-lived access keys for humans
- TLS optional, or certificate verification disabled in clients
- Encryption with a provider-default key that cannot be scoped or revoked per region

### `residency` Data residency

**Question:** Does every copy of tenant data held or produced by this component (primary, replicas, backups, snapshots, logs, metrics, dumps) stay inside the tenant's pinned region?

- Where do replicas, automated backups, manual snapshots and point-in-time recovery logs live? Is any cross-region backup copy enabled, and if so to which region and why is that lawful?
- Where do the component's logs, slow-query logs, audit logs and metrics go? Do any contain tenant data (query text with parameters, Redis keys, Temporal workflow payloads) and do they leave the region (for example a central logging account in another country)?
- Are Temporal workflow histories and payloads stored in the regional Temporal persistence store, and are payloads encrypted with a regional key via a payload codec?
- Does anyone outside the region (support staff, on-call engineers, managed-service vendors) have access to data, and is that access logged and allowed under DPDP, PDPA and client contracts?
- What policy guardrails stop resources being created in the wrong region (Service Control Policies / Azure Policy region allow-lists)?
- For India-region components, are system logs kept within India for at least the period required by CERT-In directions (180 days)?

**Good answer:** A per-region table listing each data copy (primary, replica, backup, snapshot, log, metric) with its location and retention. States that cross-region copies are disabled or, where used for disaster recovery, stay within an approved jurisdiction with the legal basis written down. Shows the organisation-level guardrail that blocks resource creation outside allowed regions and the CERT-In log retention setting for India.

**Red flags:**

- Backups copied to a different country 'for DR' with no legal review
- Central observability stack in one region receiving raw logs from all regions
- Temporal payloads stored in plain text
- No preventive guardrail, only a promise in the document

### `dr` Resilience and recovery

**Question:** Are the recovery point objective (how much data we can lose) and recovery time objective (how long we can be down) defined for this component, designed for, and proven by a recent restore drill?

- What are the RPO and RTO numbers, and do they match the platform's commitments to clients (for example hearing days, filing deadlines, SEBI ODR timelines)?
- Which failures are covered: single instance, availability zone, whole region, accidental deletion, data corruption, ransomware, loss of the cloud account? What is the response for each?
- Are backups immutable or in a separate account / vault lock so an attacker with production admin rights cannot delete them?
- When was the last full restore drill, how long did it take compared with the RTO, and how was the restored data checked for completeness (row counts, checksums, an application smoke test)?
- For Postgres: is the failover tested with PgBouncer and Prisma reconnecting cleanly? For Redis: what BullMQ jobs are lost if Redis fails, and how are they recovered? For Temporal: can workflows resume after the persistence store is restored?
- Since tenants are pinned to a region and data cannot leave it, what is the plan if a whole region is lost, and has that limit been explained to clients?
- How often are drills run (at least yearly for full restore; quarterly for failover), and where are results recorded as ISO 27001 / SOC 2 evidence?

**Good answer:** A failure-mode table with detection, automatic or manual response, expected data loss and recovery time for each scenario. RPO and RTO are stated as numbers and tied to client commitments. The latest drill is referenced with date, measured restore time and validation method, and backups are protected from deletion by a separate account or lock.

**Red flags:**

- RPO/RTO stated but never tested
- Backups in the same account and deletable by the same admin role
- No answer for region loss, or an answer that silently moves data to another country
- Redis treated as durable when it holds the only copy of job state

### `isolation` Tenant isolation and noisy neighbours

**Question:** Is the component configured so one tenant can neither see another tenant's data nor exhaust resources that other tenants depend on?

- For Postgres: is Row-Level Security forced on every tenant table (ALTER TABLE ... FORCE ROW LEVEL SECURITY), and do application roles lack BYPASSRLS and table ownership?
- For PgBouncer: is transaction pooling configured so session state cannot carry between clients (tenant set with SET LOCAL only, server_reset_query behaviour understood)?
- Which per-tenant limits exist (connection share, statement_timeout, BullMQ rate limits and concurrency per tenant, Temporal namespace or task-queue rate limits)?
- Can one tenant's large job (bulk upload, eBundle generation, transcription) starve others, and what queueing or fair-scheduling prevents it?
- Are there tenants who require dedicated infrastructure (for example a client requiring Azure or a dedicated database), and how does the IaC support that without a separate code path?
- How are Redis key namespaces and ACLs set so a compromised service cannot read other services' keys?

**Good answer:** Shows the configuration that enforces isolation at this layer (forced RLS and role grants, pooler mode, Redis ACLs) and the per-tenant limits with their numbers. Explains how heavy workloads are queued fairly and how a dedicated-infrastructure tenant is provisioned from the same IaC modules with different parameters.

**Red flags:**

- RLS enabled but not forced, or the app connects as table owner
- No statement timeout or per-tenant concurrency limits
- One global BullMQ queue with no per-tenant fairness for heavy jobs

### `iac` Infrastructure as code and change control

**Question:** Can this component be created, changed and rebuilt in every region and environment only from reviewed code, with no manual console changes?

- Which IaC module defines it (Terraform/OpenTofu, CDK, Bicep), where is the state stored and locked, and is state itself encrypted and access-restricted?
- Are regions and environments (dev, staging, prod in India, Singapore, US, plus Azure variants) produced from the same module with a parameter file each, and what are the allowed differences?
- How are changes reviewed and applied (plan in CI, approval by a code owner, apply from a pipeline identity, not a laptop)?
- How is drift detected and how often (scheduled plan, AWS Config / Azure Policy), and who is alerted?
- Which changes are risky (engine version upgrades, parameter changes needing reboot, storage changes) and what is the change process for them (maintenance window, client notice, rollback plan)?
- Are policy-as-code checks run on the plan (no public resources, encryption on, required tags, allowed regions)?

**Good answer:** Names the module path, state backend, pipeline that applies changes and the approvals required. A table lists per-region and per-cloud differences. Drift detection runs on a schedule with alert routing, and policy checks block non-compliant plans before apply.

**Red flags:**

- Resources created or modified by hand in the console
- Applies run from engineer laptops with personal credentials
- Each region has its own hand-edited copy of the code
- No drift detection

### `observability` Monitoring and alerting

**Question:** Will we learn about a problem with this component from an alert before a client tells us, and does each alert lead an on-call engineer to a concrete runbook step?

- What are the key health signals (for Postgres: replication lag, connections versus pool limits, disk, long transactions, deadlocks; for Redis: memory, evictions, BullMQ waiting and failed counts; for Temporal: schedule-to-start latency, persistence latency, workflow task failures)?
- Which alerts page someone and which only create a ticket? Are paging alerts based on user-facing symptoms and error budgets rather than every resource metric?
- Does every alert have an owner, a severity, a runbook link and a tested notification route for each region?
- Is there a synthetic check per region that exercises the component end to end?
- Are capacity alerts set early enough to act (for example disk at 70% with a growth forecast), and is certificate and credential expiry monitored?
- Where do security-relevant events go (failed logins, privilege changes, configuration changes) and are they retained per CERT-In and ISO 27001 requirements?

**Good answer:** A table of alerts: signal, threshold, severity, route, runbook link. Paging is limited to user-impacting symptoms using SLO burn-rate alerts; everything else becomes a ticket. Dashboards exist per region, synthetic checks run continuously, and audit/security logs flow to the security monitoring system in-region.

**Red flags:**

- Alerts with no runbook or no owner
- Paging on raw CPU or memory thresholds only
- No monitoring of backups succeeding or of certificate expiry

### `lifecycle` Operations and lifecycle

**Question:** Can the team run this component day to day, upgrade it before its version goes out of support, and hand it to a new on-call engineer without tribal knowledge?

- Which engine version is used (Postgres, Redis, Temporal server, PgBouncer), when does it reach end of support, and what is the upgrade plan and test approach?
- Is there a written runbook for routine tasks (scaling, failover, restore, credential rotation, adding a region, onboarding a dedicated-infrastructure tenant) and for incidents?
- Who is on call for it in each time zone covering India, Singapore and US clients, and what is the escalation path including the cloud vendor?
- How are maintenance windows chosen given hearings and deadlines across time zones, and how are tenants notified?
- What production readiness review was completed, and which items are still open?
- How is a security incident involving this component reported within the required times (CERT-In 6 hours for India, DPDP Board notification, client contractual windows)?

**Good answer:** Gives version and end-of-support dates with a scheduled upgrade, a linked runbook that has been followed by someone other than its author, the on-call rota and escalation contacts, and the status of the production readiness checklist. States the incident-reporting path with regulatory deadlines.

**Red flags:**

- Engine version already out of support or within 6 months of it with no plan
- Runbook missing or untested
- Only one person knows how to operate the component

### `cost` Cost

**Question:** Do we know what this component costs each month per region, what drives the cost as tenants grow, and who is told when it goes over budget?

- What is the monthly estimate per region and environment, broken into compute, storage, backups, data transfer, licences and support?
- What is the cost driver (per tenant, per case, per GB, per hour of hearing transcription) and what is the projected cost at 2x and 10x current volume?
- Are resources tagged with region, environment, component and (where possible) tenant so cost can be allocated, and is the tagging enforced by policy?
- Are there budgets and anomaly alerts per region, routed to a named owner?
- Which savings levers apply (reserved capacity or savings plans, right-sizing, storage tiering, turning off non-production at night) and which have been rejected because of resilience or residency needs?
- For dedicated-infrastructure or Azure tenants, is the extra cost captured in pricing?

**Good answer:** A cost table per region with a stated unit cost (for example cost per active tenant per month) and growth projection, enforced cost-allocation tags, budgets with anomaly alerts and an owner. Savings options are listed with a decision for each.

**Red flags:**

- No per-region estimate
- Cross-region data transfer costs ignored
- No budget alert, so cost overruns are found on the invoice

