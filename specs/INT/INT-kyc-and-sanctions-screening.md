---
id: "INT-kyc-and-sanctions-screening"
title: "KYC and sanctions screening provider"
parent: "INT-common-integrations"
order: 3
type: "feature"
template: "integration"
status: "draft"
owner: null
indicative: false
summary: "Identity verification and sanctions-list screening of parties and payees, with list coverage per entity and re-screening on list updates"
links: []
rev: 2
syncHash: "28f7cbae26e5eb7a"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 9.2.3 KYC and sanctions screening provider

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Identity verification and sanctions-list screening of parties and payees, with list coverage per entity and re-screening on list updates

<!-- section:purpose -->
## Purpose and use cases

Two related checks through external providers:
1. **Identity verification (KYC)** of a person or organisation where a tenant's rules or the law require it: for example verifying a party in a SEBI ODR matter, or a payee (neutral, transcriber) before the first payout.
2. **Sanctions and watch-list screening** of payees and, where the tenant enables it, of parties and paying entities, with re-screening when lists change.

Use cases: screen a neutral before empanelment payout setup ([[DOM-neutrals]]); screen a transcriber vendor; screen a refund destination ([[BIL-payment-gateway-integration]]); verify a party's identity at case registration for tenants that require it; re-screen all active payees on list updates. The obligations behind these are recorded in [[RPT-aml-kyc-sanctions-screening]]; whether Nomology or the tenant is the obligated party is a legal question per region (see questions).

<!-- section:party -->
## External party and ownership

Providers to select: an India KYC provider (PAN verification, bank account verification by penny drop, DigiLocker or offline Aadhaar XML where permitted) and a global screening provider covering the lists below. Contract owner: compliance lead. Environments: sandbox per region.

**List coverage required (proposed, to be confirmed by compliance)**

| List | Needed for |
|---|---|
| UN Security Council Consolidated List | All entities |
| US OFAC SDN and consolidated lists [R1] | All entities (US entity mandatory; others by policy) |
| India MHA lists of designated individuals and organisations (UAPA) | NTPL |
| Singapore lists under its terrorism and sanctions laws (as published by Singapore authorities) | TAPL |
| EU and UK consolidated lists | Policy choice for all entities |
| Politically exposed persons (PEP) and adverse media | Optional, per tenant |

<!-- section:flows -->
## Data flows

```
Payee bank details added / party registration requires KYC
  └─▶ Temporal workflow `{tenantId}-kyc-{subjectType}-{subjectId}`
        ├─ activity kyc.verify(subject, documents) (idempotency `kyc:{subjectId}:{checkVersion}`)
        ├─ activity screening.screen(name, DOB/year, nationality, entity type)
        ├─ result: clear ─▶ subject.kyc_status = verified / screening_status = clear
        ├─ result: possible match ─▶ human task to compliance reviewer (four-eyes for "true match" decision)
        └─ result: true match ─▶ payouts blocked, compliance escalation, record decision

List update (provider webhook or daily schedule `screening-delta-{region}` at 02:00 local)
  └─▶ re-screen all active subjects against the delta; matches ─▶ human task
```
Bank-account verification (penny drop or name match) runs before the first payout and on any bank detail change.

<!-- section:mapping -->
## Data mapping

| Our field | Provider field | Direction | Classification |
|---|---|---|---|
| subject ID `{tenantId}:{subjectId}` | client reference | out | internal |
| full name | name | out | personal |
| date of birth (or year) | DOB | out | personal; send year only if the provider accepts it |
| nationality / country | country | out | personal |
| PAN (India) | PAN | out | sensitive identifier; not stored in clear by us (masked last 4 + encrypted) |
| bank account + IFSC | account, IFSC | out | financial; encrypted at rest with per-tenant key |
| ID document images | document upload | out | sensitive; only when the tenant's rule requires document KYC |
| result status, match details, list version | response | in | sensitive; encrypted, restricted to compliance role |
| liveness / video KYC | — | not used by default | Accessible alternatives required ([[PKG-accessible-authentication-and]]) |

<!-- section:auth -->
## Authentication and secrets

API keys or OAuth client credentials per region in the regional secrets manager; webhooks for list updates verified by signature. Results are stored encrypted with the tenant's data key ([[PKG-encryption-utilities-key]]); only users with the compliance reviewer role can decrypt match details.

<!-- section:errors -->
## Errors, retries and idempotency

Payouts **fail closed**: if screening cannot complete, the payout is held and a task is created. Party KYC failures do not block filing on an open case (due process); they block only actions the tenant's rules make conditional on KYC. Retries with backoff for 5xx; validation errors (bad PAN format) go back to the user with a clear message. Duplicate list-update webhooks are de-duplicated in the inbox; re-screen jobs are idempotent per `(subjectId, listVersion)`.

<!-- section:limits -->
## Rate limits and SLAs

Expected 5,000 checks per month in Year 1 plus re-screening of all active payees on each list delta (estimated under 10,000 subjects per region). Provider list update latency requirement: within 24 hours of the list publisher (proposed).

<!-- section:residency -->
## Data transfer and compliance

Indian subjects' KYC data goes to an India-hosted provider; screening queries (name, year of birth, country) may go to a global provider, minimised to those fields, with a recorded transfer basis. Results are stored only in the tenant's region.

<!-- section:testing -->
## Sandbox and testing

Provider sandbox with documented test identities producing clear, possible-match and true-match results; no real ID documents in non-production. Scenario tests: list delta adds a name matching an active payee → payout blocked and task created.

<!-- section:questions -->
## Open questions

- [ ] Legal / compliance: for each entity and tenant type, is Nomology or the tenant the obligated party for KYC and screening, and under which law?
- [ ] Which lists are mandatory per entity (table above is a proposal)?
- [ ] Are parties (not only payees) screened, and only when the tenant enables it?
- [ ] Retention of KYC and screening records per entity (to align with [[RPT-aml-kyc-sanctions-screening]]).
- [ ] Accessible alternatives to document and liveness checks for parties with disabilities.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant separation at the provider

Subjects are referenced as `{tenantId}:{subjectId}`; a neutral empanelled with two tenants is screened separately per tenant (no cross-tenant sharing of results) unless legal approves a shared platform-level screening record without case data.

<!-- check:residency -->
### Data transfer and residency

India KYC in India; screening queries minimised to name, year of birth and country; results stored only in the tenant region.

<!-- check:vendor -->
### Vendor risk and exit

Selection criteria: list coverage per the table with update latency under 24 hours, ISO 27001 or SOC 2 Type II, in-region processing for India KYC, contractual no-training and deletion on exit, audit log export of each screening with list version.

<!-- check:resilience -->
### Failure handling and degradation

Payouts fail closed when screening is unavailable; party flows fail open for due-process actions. Retries and idempotency per subject and list version.

<!-- check:audit -->
### Audit and evidence

Each check stores request summary (fields sent, not full documents), provider reference, list versions, result, reviewer decision with reason, and timestamps, encrypted in-region. Four-eyes on true-match decisions.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Official search of the SDN and other OFAC sanctions lists.",
    "id": "R1",
    "kind": "web",
    "publisher": "US Department of the Treasury, OFAC",
    "retrieved": "2026-10-28",
    "title": "OFAC Sanctions List Search",
    "url": "https://sanctionssearch.ofac.treas.gov/"
  }
]
```

<!-- end -->
