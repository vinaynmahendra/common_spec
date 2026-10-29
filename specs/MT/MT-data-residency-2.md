---
id: "MT-data-residency-2"
title: "Data residency"
parent: "MT"
order: 4
type: "capability"
template: "design"
status: "draft"
owner: null
indicative: false
summary: "Each tenant is pinned to one region (India, Singapore, US); one shared database and full regional stack per region; global tenant directory and routing of every request, job and workflow to the home region; rules for moving a tenant between regions"
links: []
rev: 3
syncHash: "8c7c265a69370db1"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 3.4 Data residency

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Each tenant is pinned to one region (India, Singapore, US); one shared database and full regional stack per region; global tenant directory and routing of every request, job and workflow to the home region; rules for moving a tenant between regions

<!-- section:context -->
## Context and scope

Nomology serves institutions in India, Singapore and the US through three entities (NTPL in India, TAPL in Singapore, and a US entity). Clients and regulators expect case data to stay in a stated country: Indian ODR institutions working under SEBI's ODR framework, arbitral institutions with their own data commitments to parties, and enterprise clients with contractual residency clauses. Several decisions already fix the shape: Next.js self-hosted per region ([[ADR-next-js-hosting]]), Temporal self-hosted per region ([[ADR-temporal]]), ECS per region or Azure Container Apps where required ([[ADR-container-orchestration]]), and one shared database per region with RLS ([[ADR-tenant-isolation]]).

What exists today: no regional stacks yet. What this note designs: how a tenant is pinned to a region, what is regional and what is global, how every request, job and workflow is routed to the home region, and how a tenant is moved between regions.

This note also absorbs the earlier item "one shared database per region; tenants are pinned to their region's database".

<!-- section:goals -->
## Goals and non-goals

**Goals**

- G1. Each tenant has exactly one home region (`in`, `sg`, `us`, or an Azure region code such as `in-az`), recorded in the tenant row and the global directory.
- G2. All tenant personal and case data — database rows, files, search indexes, embeddings, caches, workflow history, backups and logs — is stored and processed only in the home region, except transfers to sub-processors that are recorded in [[SEC-vendor-sub-processor-management]].
- G3. Every request, BullMQ job and Temporal workflow runs in the home region; a request that arrives elsewhere is redirected without touching tenant data.
- G4. Regions are independent: loss of one region does not stop the others ([[SEC-business-continuity]]).
- G5. A tenant can be moved between regions by a rehearsed, auditable procedure with a bounded read-only window.

**Non-goals**

- Active-active or multi-region replication of a tenant's data (that would break residency).
- A global user identity across regions in Phase 1.
- Cross-region failover of a tenant's data to another country; disaster recovery stays inside the home country unless a client contract allows otherwise ([[INF-backup-and-disaster-recovery]]).
- Per-tenant databases (see [[ADR-tenant-isolation]]).

<!-- section:design -->
## Design

#### Regional and global components

| Component | Scope | Holds personal data? | Notes |
|---|---|---|---|
| Postgres primary + replicas, PgBouncer | Per region | Yes | One shared database per region with forced RLS |
| Redis (BullMQ, cache) | Per region | Transient | Tenant-scoped keys ([[PKG-caching]]) |
| Temporal cluster, namespace `prod-<region>` | Per region | Yes (encrypted payloads) | Payload codec keys per region (guardrails in [[WF-separation-of-concerns-temporal]]) |
| App and worker containers (ECS / Azure Container Apps) | Per region | Process only | `TENANCY_REGION` env pins them |
| Object storage, KMS keys, secrets | Per region | Yes | Bucket per region; tenant prefix; keys never leave region |
| Search / vector store | Per region | Yes | Tenant-scoped indexes |
| Logs, traces, metrics backends | Per region | Logs may contain ids, not content | India logs retained in India for CERT-In purposes [R1] |
| Reporting replica / warehouse | Per region | Yes | Cross-region totals from aggregates only |
| **Tenant directory** | Global | No (slug, hostnames, region, status, type) | Source of truth for routing; replicated read-only copy in each region |
| DNS / CDN | Global | Transit only (TLS terminated at regional origin; CDN caches only static assets) | Routes host → regional origin |
| CI/CD, source code, container registry | Global | No | Images contain no data |
| Status page, staff identity provider | Global | Staff data only | Staff are Nomology employees, not tenant users |

#### Tenant directory

```ts
interface DirectoryEntry {
  tenantId: string;            // uuid
  slug: string;
  hostnames: string[];         // subdomain + verified custom domains
  region: 'in' | 'sg' | 'us' | string;
  status: 'provisioning' | 'active' | 'suspended' | 'offboarding' | 'deleted';
  type: string;
  version: number;             // monotonic, for cache invalidation
}
```

Each regional database publishes changes to its `tenant` and `tenant_domain` rows through an outbox to the directory service; the directory service replicates entries to a read-only copy in every region, which `@nomology/tenancy` reads ([[MT-tenant-resolution]]). Slug uniqueness is reserved in the directory before a tenant row is created (TM-R2 in [[MT-tenant-model]]).

#### Routing

1. **Web**: DNS for `{slug}.{product-domain}` and custom domains points at the CDN; the CDN routes by host to the regional origin using the directory (edge configuration generated from the directory). If a request still reaches the wrong region, middleware redirects (307) to the correct regional host without reading tenant data.
2. **Public and aggregator API**: API hostnames are regional (`api.in.<domain>`, `api.sg.<domain>`, `api.us.<domain>`); a credential issued in one region is unknown in another. A call to the wrong region returns `421` with problem type `wrong-region` and the correct base URL.
3. **Webhooks inbound** (payment gateways, messaging providers): each region registers its own callback URLs with providers.
4. **Jobs**: BullMQ queues are regional; `toEnvelope()` stamps the region and `runWithTenant` refuses a mismatched region.
5. **Workflows**: started only by the regional Temporal client; workflow ID `{tenantId}-{process}-{entityId}`; the tenant's region is fixed for the life of the workflow.
6. **AI calls**: the AI gateway selects a model endpoint in or approved for the tenant's region ([[AI-ai-gateway]]); a tenant can opt out of any AI processing outside its region.
7. **Email / SMS / WhatsApp and video**: providers are chosen per region ([[INT-messaging-providers]], [[INT-video-conferencing-for-hearings]]); where a provider processes outside the region, it is recorded as a transfer.

#### Users across regions

A person who acts for tenants in two regions has a separate user account in each region (TM-R3). The sign-in page of each regional host signs into that region only. A global identity index (email → regions) would itself be personal data held globally, so it is not built in Phase 1.

#### Moving a tenant between regions

Moving a tenant is a transfer of personal data across borders and needs legal approval for both regions and the tenant's written instruction. Procedure, run as a Temporal workflow in the platform-ops task queue of the source region, coordinated with a twin in the target region:

1. **Approve**: legal sign-off and tenant instruction recorded; target region provisioned as an empty tenant shell with the same `tenant_id`.
2. **Quiesce**: tenant set to `suspended` with reason `region_move` (read-only); new jobs refused; open Temporal workflows are either allowed to reach a safe point or cancelled, and their business state (deadlines, pending human tasks) is captured from domain tables, not from Temporal history, because running workflows cannot be moved between clusters.
3. **Copy**: export all tenant-owned rows by `tenant_id` (logical export as `nomo_platform_ops`), object storage by prefix, re-encrypt with target-region keys; load in target; rebuild search and vector indexes.
4. **Verify**: row counts and checksums per table; object counts and content hashes; isolation tests against the moved tenant.
5. **Switch**: directory entry region updated; DNS / CDN routing follows; workflows recreated from domain state in the target region.
6. **Clean up**: source data deleted after a soak period (30 days proposed) unless the tenant asks earlier; source backups age out; deletion certificate issued.

Target read-only window: under 8 hours for a tenant with up to 1 TB of objects (proposed, to be measured).

<!-- section:examples -->
## Worked examples

**SEBI ODR institution tenant in India.** `odr-alpha` is created with `home_region = 'in'`. An MII calls `POST https://api.in.<domain>/aggregator/v1/matters` with 2,000 matters. The aggregator credential exists only in the India region; each matter creates rows in the India database, notices are queued in India's BullMQ, and the `{tenantId}-case-lifecycle-{caseId}` workflows run on Temporal `prod-in`. Investor SMS goes through the India SMS provider with DLT-registered templates ([[PKG-notification-copy]]).

**Singapore arbitral institution with a US-based counsel.** Tenant `acia` is in `sg`. A counsel in New York opens `acia.<product-domain>`; the CDN routes to the Singapore origin; the counsel's account exists in the Singapore region only. Their latency is higher, but their data and the case data stay in Singapore.

**Wrong region.** A bookmarked link `https://us.<domain>/t/acia/cases/123` reaches the US region. Middleware resolves `acia` → `sg` from the directory replica and returns `307` to the Singapore host. No US database query is made.

<!-- section:alternatives -->
## Alternatives considered

| Alternative | Why not chosen |
|---|---|
| One global stack with region tags on rows | Data would physically sit in one country; fails residency commitments |
| Database per tenant within a region | Operational cost and migration complexity at hundreds of tenants; rejected in [[ADR-tenant-isolation]] |
| Global identity with regional data | Requires global personal data (email index); deferred pending legal view |
| Cross-region read replicas for DR | Moves data out of country; DR stays in-country (second availability zone / second in-country region where one exists) |
| Edge-hosted middleware at a vendor | Self-hosting decided in [[ADR-next-js-hosting]]; CDN does routing only |

<!-- section:crosscutting -->
## Cross-cutting concerns

- **Security**: regional KMS keys and secrets; the directory holds no secrets and no personal data; directory writes are authenticated per region with mutual TLS.
- **Privacy**: transfers outside the home region happen only via recorded sub-processors; the record of processing lists region per processing activity ([[SEC-privacy-controls]]). GDPR Chapter V and PDPA transfer limitation apply where EU or Singapore personal data leaves those jurisdictions [R2][R3].
- **Tenancy**: region is a property of the tenant, never of a user's location.
- **Observability**: each region has its own telemetry backend; a global operations view shows per-region aggregates (counts, latencies, error rates) tagged by `tenant_id` but without content ([[OBS-foundations]]).
- **Cost**: three full stacks from Phase 1; staging can share fewer instances but must keep the same topology so routing is tested.

<!-- section:guardrails -->
## Guardrails

- Never add a global data store containing tenant data; any new global component needs an ADR stating it holds no personal or case data.
- Every container must have `TENANCY_REGION` and refuse to start without it.
- Every queue name, Temporal namespace, bucket and index name includes the region code.
- No code path may call another region's database, Redis, Temporal or storage. Network policy blocks cross-region data-plane traffic; only the directory replication channel crosses regions.
- Logs and traces must not contain case content or personal data beyond ids; this keeps any global aggregation safe.
- A region move is a workflow, never a manual script.

<!-- section:ownership -->
## Ownership

| Part | Owner |
|---|---|
| Directory service and routing | Platform engineering |
| Regional stacks and network policy | DevOps ([[INF-cloud-and-iac]]) |
| Transfer assessments and sub-processor records | DPO / legal ([[SEC-vendor-sub-processor-management]]) |
| Region move approvals | CTO + legal + tenant |

<!-- section:questions -->
## Open questions

- [ ] Which cloud regions per country (for example AWS Mumbai / Hyderabad for India, Singapore, a US region) and whether DR uses a second in-country region. Owner: DevOps with CTO.
- [ ] Where is the directory's primary hosted, and is an institution's name and domain acceptable as global data? Assumption: not personal data; to be confirmed by legal.
- [ ] Global identity index: needed, and if so, where may it live? Owner: CTO with legal.
- [ ] Which client contracts require Azure, and in which regions? Each becomes its own region code.
- [ ] AI model endpoints per region and the tenant opt-out default for out-of-region AI processing. Owner: [[AI-ai-gateway]].
- [ ] Merged item "one shared database per region; tenants pinned to their region's database" has been folded into the design above; remove after review.

<!-- checks -->
## Template checks

<!-- check:security -->
### Security and privacy

New surface: the directory service and its replication channel, and regional redirects. Threats: directory tampering (redirecting a tenant's traffic), mitigated by authenticated writes from regional outboxes only, signed entries, and alerts on region changes outside the move workflow; open redirect via the wrong-region path, mitigated by redirecting only to hosts from the configured regional host map.

<!-- check:tenancy -->
### Tenancy

Tenant id and region travel together in the request context, job envelope and workflow input; each region refuses work for tenants that are not its own. Within a region, isolation is as in [[MT-isolation-strategy]].

<!-- check:residency -->
### Data residency and lifecycle

Yes by design: every store listed as regional keeps tenant data in the home region; global components hold no tenant personal data; backups and logs stay in-region (for India, logs kept in India for CERT-In's 180-day requirement [R1]). Exceptions are sub-processors with recorded transfers.

<!-- check:failure -->
### Failure handling and recovery

Loss of the directory: regions serve from their replica cache (10 minutes stale) and then fail closed for new hosts only; existing sessions continue. Loss of a region: only that region's tenants are affected; recovery follows [[INF-backup-and-disaster-recovery]] within the same country. A failed region move stops before the switch step and the tenant is reinstated in the source region.

<!-- check:rollout -->
### Rollout and migration

India region first (Phase 1), then Singapore and US with the same IaC modules; staging mirrors the three-region topology so wrong-region and directory tests run before production. The region move procedure is rehearsed in staging before the first real move.

<!-- check:reversibility -->
### Reversibility

Hard to change later: one-account-per-region identity, region codes embedded in names, and the decision that DR stays in-country. These should be recorded as ADRs before Phase 1 ends.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Report specified cyber incidents to CERT-In within 6 hours of noticing them; keep logs of ICT systems for 180 days within Indian jurisdiction; synchronise clocks to NTP servers of NIC or NPL; designate a point of contact.",
    "id": "R1",
    "issuer": "CERT-In, Ministry of Electronics and IT",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Directions under section 70B(6) of the IT Act, 2000 (28 April 2022)",
    "title": "CERT-In Directions relating to information security practices, procedure, prevention, response and reporting of cyber incidents",
    "url": "https://www.cert-in.org.in/Directions70B.jsp"
  },
  {
    "excerpt": "Art. 12(3) one month to respond to requests (extendable by two months); Arts 13–14 information; Arts 15–22 rights; Art. 28 processors; Art. 30 records; Art. 32 security; Art. 33 notify the supervisory authority within 72 hours; Art. 34 communicate to data subjects; Chapter V transfers.",
    "id": "R2",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU / EEA",
    "kind": "regulation",
    "ref": "Regulation (EU) 2016/679",
    "title": "General Data Protection Regulation",
    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng"
  },
  {
    "excerpt": "Personal data transferred outside Singapore must receive a standard of protection comparable to the PDPA.",
    "id": "R3",
    "issuer": "Personal Data Protection Commission, Singapore",
    "jurisdiction": "Singapore",
    "kind": "regulation",
    "ref": "Advisory Guidelines on Key Concepts in the PDPA, Chapter 19",
    "title": "The Transfer Limitation Obligation",
    "url": "https://www.pdpc.gov.sg/-/media/files/pdpc/pdf-files/advisory-guidelines/the-transfer-limitation-obligation---ch-19-(270717).pdf"
  }
]
```

<!-- end -->
