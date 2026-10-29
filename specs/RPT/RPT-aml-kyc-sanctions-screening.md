---
id: "RPT-aml-kyc-sanctions-screening"
title: "AML, KYC, sanctions screening"
parent: "RPT-statutory"
order: 2
type: "requirement"
template: "regulatory"
status: "draft"
owner: null
indicative: false
summary: "Screening register, match dispositions and escalation packs for parties and payees screened against sanctions lists (OFAC, UN, India MHA and others); external filings only where counsel confirms an obligation"
links: []
rev: 3
syncHash: "034d8ae236dadcac"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 12.2.1.2 AML, KYC, sanctions screening

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Screening register, match dispositions and escalation packs for parties and payees screened against sanctions lists (OFAC, UN, India MHA and others); external filings only where counsel confirms an obligation

<!-- section:obligation -->
## Obligation and source

Status: **assumed, counsel to confirm.** Screening itself is provided by [[INT-kyc-and-sanctions-screening]]; this node specifies the records, reports and escalations built from it.

Working assumptions (each an open question):
- NTPL, TAPL and the US entity are **not** reporting entities under India's PMLA or equivalent AML regimes, because they do not hold or move client funds; payments go through regulated payment gateways ([[BIL-payment-gateway-integration]]). If this changes (for example escrow of settlement amounts), suspicious transaction reporting to FIU-IND in the prescribed formats [R1] would need its own node.
- The US entity, as a US person, must not deal with persons on OFAC sanctions lists and may have reporting duties if it blocks or rejects a transaction. Exact duties to be confirmed by US counsel.
- India (UN Security Council and MHA designations under counter-terrorism law) and Singapore (UN and Singapore designations) impose prohibitions and, in some cases, duties to inform authorities if a person holds information about designated persons' property. Exact duties to be confirmed by counsel per entity.
- Some tenants (for example institutions handling cross-border arbitrations, or SEBI ODR matters with payouts) may contractually require screening records from the platform.

<!-- section:applicability -->
## Applicability

Screened populations (proposal): parties and their representatives at case registration and on party change; payees of refunds, neutral and transcriber payouts before payment; neutrals and transcribers at onboarding. Lists by entity: US entity — OFAC SDN and consolidated lists; NTPL — UN Security Council consolidated list and MHA designated lists; TAPL — UN list and Singapore designations; plus any lists a tenant requires. Re-screening on every list update for open cases and active payees.

<!-- section:recipient -->
## Recipient and channel

Internal: Nomology compliance officer per entity (escalation queue in `/(platform-admin)/compliance/screening`), and tenant compliance contact where the tenant requires it. External: only after counsel confirms an obligation (for example a US blocking or reject report, or a disclosure to Indian or Singapore authorities); the named officer submits.

<!-- section:frequency -->
## Frequency and deadlines

- Event-driven escalation: a potential match that is not cleared as a false positive within 1 business day (proposed) is escalated; a confirmed match blocks the related payment or action immediately and opens an escalation pack.
- Periodic internal report: monthly screening summary per entity and tenant (coverage, matches, dispositions, overdue reviews).
- External deadlines: to be set per confirmed obligation.

<!-- section:fields -->
## Field mapping

**Screening register** (`screening_checks`, tenant-owned, RLS):

| Field | Source | Validation |
|---|---|---|
| Check ID | generated | unique |
| Subject type | party, representative, payee, neutral, transcriber | required |
| Subject reference | `case_parties.id` / payee ID | required |
| Name and identifiers screened | snapshot of name, DOB / registration no., country | minimum fields per list rules |
| Lists and list versions | provider response | required |
| Trigger | registration, change, list update, pre-payment | required |
| Result | no match / potential match / confirmed match | required |
| Disposition, reviewer, reason, time | review UI | reviewer ≠ system; reason required for clearance |

**Monthly summary** (internal report): checks performed by trigger; subjects not screened that should have been (coverage gap); potential matches opened, cleared, escalated; median time to disposition; payments held.

**Escalation pack** (per confirmed match): subject details, list entry matched, related cases and payments, actions taken (payment held, case action paused), timeline, reviewer notes.

<!-- section:validation -->
## Validation and reconciliation

- Coverage: every party registered and every payout in the period has a screening check before the action (coverage gap must be 0; any gap is itself an escalation)
- Every potential match has a disposition or is in the overdue list
- List versions used are no older than the provider's latest by more than 24 hours (proposed)

<!-- section:workflow -->
## Preparation, approval and submission

Screening runs as BullMQ jobs (`screening-check`); re-screening on list update as a Temporal workflow per region. Dispositions are maker-checker for confirmed matches (reviewer and approving compliance officer differ). Escalation packs use the shared pipeline in [[RPT-regulatory-and-aggregator#workflow]] when an external submission is confirmed.

<!-- section:evidence -->
## Evidence and retention

Screening register retained for the period counsel sets (assumption: at least 5 years after case close or payment); escalation packs in the object-locked evidence bucket in the entity's region.

<!-- section:questions -->
## Open questions

- [ ] Counsel: confirm that no Nomology entity is a reporting entity under PMLA (India) or equivalent, and under what business change that would flip
- [ ] US counsel: OFAC duties for the US entity (blocking and reject reporting, timelines)
- [ ] India / Singapore counsel: duties on a confirmed match to UN / MHA / Singapore designations
- [ ] Which tenants require screening records and in what form
- [ ] Retention period for screening records

<!-- checks -->
## Template checks

<!-- check:completeness -->
### Completeness

Coverage is reconciled monthly: every party registered and every payout must have a check before the action; the summary lists any gap as an exception rather than hiding it.

<!-- check:segregation -->
### Tenant and entity segregation

Screening records are tenant-owned with forced RLS; the entity-level monthly summary runs under the platform reader role over counts only; escalation packs are kept in the entity's region.

<!-- check:security -->
### Access, approval and transmission

Confirmed-match escalations are restricted to the compliance officer and approver; the subject and the tenant's ordinary users cannot see that an escalation exists. If an obligation to report to FIU-IND ever applies, tipping-off restrictions would need the same treatment [R1].

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Reporting formats used by reporting entities under PMLA for CTR, STR and related reports.",
    "id": "R1",
    "issuer": "Financial Intelligence Unit - India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "FIU-IND Reporting Format Guide",
    "title": "FIU-IND Reporting Format Guide",
    "url": "https://fiuindia.gov.in/pdfs/quicklinks/Reporting_Format.pdf"
  }
]
```

<!-- end -->
