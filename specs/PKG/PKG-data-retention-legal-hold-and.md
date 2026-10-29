---
id: "PKG-data-retention-legal-hold-and"
title: "Data retention, legal hold and deletion"
parent: "PKG"
order: 15
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "Shared retention schedules per entity type and tenant, legal holds that block every deletion path, deletion and anonymisation jobs across Postgres, storage, search, embeddings, logs and backups"
links: []
rev: 3
syncHash: "2c2120d629dbca7b"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.15 Data retention, legal hold and deletion

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Shared retention schedules per entity type and tenant, legal holds that block every deletion path, deletion and anonymisation jobs across Postgres, storage, search, embeddings, logs and backups

<!-- section:purpose -->
## Purpose and scope

`@nomology/retention` makes data leave the platform when it should, and only when it should. It holds retention schedules per record type and tenant, places and releases legal holds that block every deletion path, and runs deletion and anonymisation across every store where a tenant's data lives: Postgres tables, object storage, search indexes, AI embeddings, caches, logs and the audit archive. Backups expire on their own schedule ([[INF-backup-and-disaster-recovery]]).

Triggers: retention clock expiry (for example N years after case closure), data principal erasure requests ([[SEC-data-principal-rights-requests]]), tenant offboarding ([[MT-tenant-lifecycle]]), and withdrawal of uploads before service.

**Does not:** decide legal periods (legal sets them in [[PKG-retention-and-deletion-schedule]]); answer access requests (the rights workflow does, using catalogue data from here and [[PKG-metadata-management-entity]]).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use |
|---|---|
| Nightly retention sweep (Temporal schedule per region) | Find records past their retention end and delete or anonymise them, in batches per tenant |
| Rights request workflow | Erase or anonymise one person's data where no legal-record exemption or hold applies; produce a report of what was kept and why |
| Tenant offboarding workflow | Export, then delete all tenant data after the contractual period; crypto-shred keys |
| Secretariat / legal at the tenant | Place and release legal holds on cases, parties or the whole tenant |
| Storage, search, audit, AI packages | Call `checkHolds` before deleting anything; receive deletion requests through the outbox |

<!-- section:api -->
## Public API

```ts
// packages/retention/src/index.ts (server-only)
export type HoldScope = { type: 'tenant' } | { type: 'case'; id: string } | { type: 'party'; id: string } | { type: 'user'; id: string } | { type: 'document'; id: string };

export function placeHold(tx: TenantTx, p: { scope: HoldScope; reason: string; reference?: string; requestedBy: string }): Promise<{ holdId: string }>;  // step-up; permission data.legal_hold:create
export function releaseHold(tx: TenantTx, holdId: string, p: { reason: string }): Promise<void>;                                               // second approver required
export function activeHolds(tx: TenantTx, target: RecordRef): Promise<HoldSummary[]>;

/** Every deletion path must obtain a token; storage.deleteObject and repository hard-deletes require it. */
export function checkHolds(tx: TenantTx, target: RecordRef): Promise<HoldCheckToken>;    // throws LegalHoldActiveError
export type HoldCheckToken = { tokenId: string; target: RecordRef; checkedAt: Date; expiresAt: Date };  // valid 15 minutes, single target

/** Schedules (data from PKG-retention-and-deletion-schedule; tenant may extend, never shorten below platform minimum) */
export function effectivePolicy(tx: TenantTx, recordType: RecordType): Promise<RetentionPolicy>;
export function setTenantExtension(tx: TenantTx, recordType: RecordType, years: number, reason: string): Promise<void>;

/** Runs */
export function planRun(tx: TenantTx, p: { trigger: 'schedule' | 'erasure_request' | 'offboarding'; subject?: SubjectRef; dryRun: boolean }): Promise<RunPlan>;
export function executeRun(planId: string): Promise<{ runId: string }>;     // starts Temporal workflow 'retention-run'
export function runReport(tx: TenantTx, runId: string): Promise<RunReport>;  // per store: deleted, anonymised, kept (reason), failed

/** Registration: each package declares its stores and how to delete/anonymise by record type */
export function registerStore(def: {
  store: 'postgres' | 'object_storage' | 'search' | 'embeddings' | 'cache' | 'audit_archive' | 'logs';
  recordTypes: RecordType[];
  find: (tx: TenantTx, sel: Selection) => AsyncIterable<RecordRef>;
  erase: (tx: TenantTx, ref: RecordRef, mode: 'delete' | 'anonymise', token: HoldCheckToken) => Promise<void>;  // idempotent
}): void;

export class LegalHoldActiveError extends Error { readonly holds: HoldSummary[] }
```

The `retention-run` Temporal workflow ([[WF-separation-of-concerns-temporal]] layers): Activity `listCandidates` (per store, batched) → Activity `checkHolds` → Activity `erase` per batch (heartbeats) → Activity `verify` (candidates no longer present) → Activity `writeReport`. Dry runs stop after `checkHolds` and write the report.

<!-- section:usage -->
## Usage examples

```ts
// Secretariat lead places a hold because a set-aside application was filed in court
await withTenant((tx) => retention.placeHold(tx, {
  scope: { type: 'case', id: caseId }, reason: 'Set-aside application pending', reference: 'Court ref (as provided)', requestedBy: userId,
}));

// Inside a package's erase function
const token = await retention.checkHolds(tx, { type: 'document_version', id });
await storage.deleteObject(ref, { allVersions: true, reason: 'retention_expired', holdCheckToken: token });
```

<!-- section:tenant -->
## Tenant context

Policies, holds, runs and reports are tenant-owned tables under forced RLS ([[PKG-retention-and-deletion-schedule#tenancy]]). Sweeps iterate tenants with `forEachTenant` and run each tenant's work in its own context; there is no cross-tenant deletion query. A tenant-scope hold blocks every deletion for that tenant, including offboarding deletion. Platform staff cannot release a tenant's holds.

<!-- section:config -->
## Configuration

| Setting | Default (proposed) | Who |
|---|---|---|
| Platform minimum periods per record type | From [[PKG-retention-and-deletion-schedule]] | Legal / DPO via PR |
| Tenant extensions | Allowed upward only | Tenant admin with step-up and reason |
| Sweep schedule | Nightly 01:00 region local time | Platform |
| Enable destructive runs | Off per region until legal approves dry-run reports (flag `retention.destructive.<region>`) | Platform security + legal |
| Batch size | 500 records per Activity, heartbeat every 50 | Platform |
| Hold-check token validity | 15 minutes | Platform |

<!-- section:adapters -->
## Providers and extension points

Stores register through `registerStore`. Shipped registrations: domain repositories (Postgres hard delete or anonymise columns), storage (`deleteObject` all versions, Object Lock legal holds for WORM classes), search (`delete` by entity), AI embeddings ([[AI-rag]] vector store delete by source document), cache (`bumpNamespace` for user scopes), audit archive (per-tenant archive object deletion at end of period), logs (log retention is time-based in the log store; no per-record deletion — documented as a limitation).

<!-- section:errors -->
## Error model

| Error | Retryable | Handling |
|---|---|---|
| `LegalHoldActiveError` | No | Record kept; listed in report as `kept: legal_hold` |
| Store unavailable | Yes (Temporal Activity retry with backoff) | Run continues other stores; report marks partial |
| Verification mismatch (record still present) | No | Run marked failed; alert DPO and platform on-call |
| Token expired | Yes | Re-check holds |

<!-- section:nfr -->
## Performance and limits

Sweep throughput ≥ 10,000 records per minute per region; an erasure request for one person completes within 7 days of approval (proposed internal target, well within statutory response windows — legal to confirm); offboarding deletion of a large tenant completes within 30 days after the retention date.

<!-- section:versioning -->
## Versioning and compatibility

Semver. Schedules are versioned data in the schedule node; a change to a period applies to records whose clock has not yet expired at the time of change, and the run report records the schedule version used.

<!-- section:testing -->
## Test contract

- Hold blocks every registered store's erase (contract test each store must pass).
- Dry-run vs destructive parity: the destructive run deletes exactly the dry-run plan minus newly held records.
- Idempotency: re-running a completed run deletes nothing new and reports the same totals.
- Anonymisation keeps the legal record readable (case history intact) while personal fields are replaced.
- Isolation: a run for tenant A never touches tenant B.

<!-- section:questions -->
## Open questions

- [ ] Legal to confirm periods per record type and tenant type (arbitral institution, SEBI ODR institution, CORD), including whether institutions keep awards permanently.
- [x] Who at a tenant may place and release holds? Answered by the permission catalogue: `data.legal_hold:create` and `data.legal_hold:delete` (release needs maker-checker), held by `security_admin` and `tenant_owner` through `ps.admin.data`, and grantable to a custom role cloned from the managed template `secretariat_lead` ([[PKG-permission-catalogue]], [[PKG-roles-and-permission-sets]]). No separate `tenant_legal` role is needed.
- [ ] Logs cannot be erased per record; confirm that time-based log retention with no case content in logs is acceptable to the DPO.
- [ ] Backups: confirm the statement for privacy notices that deleted data persists in encrypted backups until they expire (for example 35 days).

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

All retention data is tenant-owned under forced RLS; sweeps use `forEachTenant`; holds and runs are tenant-scoped; there is no global delete query.

<!-- check:data-protection -->
### Personal data handling

This package is the mechanism for storage limitation and erasure: every store registers its delete or anonymise path; legal holds and legal-record exemptions are recorded per record in run reports, which are the evidence for responses to data principals and regulators.

<!-- check:audit -->
### Audit events

Hold placement and release (with approvers), policy extensions, run plans, executions and reports are audited; deletion events record counts and record IDs, never the deleted content.

<!-- check:resilience -->
### Failure behaviour

Runs are Temporal workflows with idempotent, heartbeating Activities; re-running is safe; partial failures are reported per store and retried; destructive runs are behind a per-region flag.

<!-- check:change-safety -->
### Change and release safety

Destructive deletion is disabled per region until legal reviews dry-run reports; schedule changes are versioned; new stores must pass the hold contract test before registration is accepted.

<!-- check:testing -->
### Testing

Hold contract test per store, dry-run parity, idempotency and anonymisation tests, all against real Postgres, LocalStack storage and the search backend.

<!-- end -->
