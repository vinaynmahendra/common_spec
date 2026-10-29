---
id: "PKG-audit-trail"
title: "Audit trail"
parent: "PKG"
order: 10
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "immutable, tamper-evident log of every user and system action"
links: []
rev: 3
syncHash: "fbcc2e7e9c7065b0"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.10 Audit trail

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> immutable, tamper-evident log of every user and system action

<!-- section:purpose -->
## Purpose and scope

`@nomology/audit` records who did what, to which record, when, from where and under which policy or rule version, for every user and system action that changes state, grants or uses access, reveals sensitive data or sends something to a person. Records are append-only for the application, written in the same transaction as the change, sealed into hash-chained batches and anchored to write-once storage so tampering is detectable.

It serves three audiences: institutions (a secretariat proving the history of a case, for example to a court reviewing an award), Nomology security and compliance (ISO 27001 and SOC 2 evidence, incident investigation), and data principals (access requests that ask what was done with their data).

**Does not:**
- Replace domain history. Case status events, document versions and invoice states are owned by their domain schemas ([[DOM-cases-schema]], [[DOM-documents-schema]]); audit records reference them.
- Store document content or full personal data. Events store identifiers, field names changed and hashes of before/after values; the rule is in [[PKG-audit-log-schema#protection]].
- Act as the security monitoring system. Security-relevant events are also forwarded to the SIEM pipeline in [[OBS-security-events]].

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use case |
|---|---|
| All domain write paths (Server Actions, tRPC, Temporal Activities) | `audit.record(tx, ...)` inside the same `withTenant` transaction as the change |
| Authorisation ([[PKG-authorization]]) | Denials of sensitive actions, role grants, ethical wall overrides, support access sessions |
| Authentication ([[PKG-authentication]]) | Sign-in, MFA enrolment and reset, SSO configuration changes, session revocation |
| Storage ([[PKG-encryption-at-rest-signed-urls]]) | Signed URL issued for award drafts, KYC documents and other tribunal-only or sensitive files (reads are audited) |
| Tenant admin console ([[APP-tenant-admin-console]]) | Tenant-scoped audit search and export for their own tenant |
| Secretariat console | Case history export ("who did what on case X") |
| Data principal rights ([[SEC-data-principal-rights-requests]]) | Find events about one person for access requests |
| Support access ([[PKG-support-access-and-impersonation]]) | Tenant-visible list of every support action |

<!-- section:api -->
## Public API

```ts
// packages/audit/src/index.ts  (server-only)
import type { TenantTx } from '@nomology/db';

export type AuditAction = `${string}.${string}`;   // registered in the action catalogue, e.g. 'case.party.added'
export type AuditCategory = 'data_change' | 'access' | 'auth' | 'admin' | 'communication' | 'export' | 'system';

export interface AuditEventInput {
  action: AuditAction;
  target: { type: string; id: string; caseId?: string };     // caseId enables case-history export
  outcome?: 'success' | 'denied' | 'failure';                 // default 'success'
  reason?: string;                                             // free text, max 500 chars, required for overrides
  changes?: FieldChange[];                                     // field names + hashed values, never raw personal data
  policy?: { id: string; version: string };                    // authz policy or rules decision version
  subjects?: { type: 'user' | 'party'; id: string }[];         // data principals affected (for rights requests)
  meta?: Record<string, string | number | boolean>;            // validated per action; no free-form objects
}
export interface FieldChange { field: string; before?: AuditValue; after?: AuditValue }
export type AuditValue = { hash: string } | { value: string | number | boolean | null }; // value only for fields tagged non-personal

/** Write one event in the caller's transaction. Actor, tenant, region, request and trace IDs come from context. */
export function record(tx: TenantTx, evt: AuditEventInput): Promise<{ id: string }>;

/** For the rare paths with no DB transaction (e.g. failed sign-in before a tenant user is known). Uses its own short transaction. */
export function recordStandalone(evt: AuditEventInput & { tenantId: string }): Promise<{ id: string }>;

/** Platform-level events (no tenant): tenant provisioning, platform role changes, break-glass. */
export function recordPlatform(evt: AuditEventInput): Promise<{ id: string }>;

/** Query and export (tenant-scoped; caller must hold audit.read / audit.export) */
export function search(tx: TenantTx, q: AuditQuery): Promise<Page<AuditEventView>>;
export function exportEvents(q: AuditQuery & { format: 'jsonl' | 'csv' }): Promise<{ exportId: string }>; // async, BullMQ; result is a signed URL
export function caseHistory(tx: TenantTx, caseId: string): AsyncIterable<AuditEventView>;

/** Verification */
export function verifyRange(tenantId: string, from: Date, to: Date): Promise<VerifyReport>;   // recompute hashes and Merkle roots, compare with anchors

/** Action catalogue registration (compile-time list per package) */
export function defineActions<T extends Record<AuditAction, ActionDef>>(defs: T): T;
export interface ActionDef { category: AuditCategory; description: string; sensitiveRead?: boolean; requiresReason?: boolean; metaSchema?: import('zod').ZodTypeAny }

export class UnknownAuditActionError extends Error {}
export class AuditWriteError extends Error {}   // the surrounding transaction must roll back
```

Events emitted by the package itself (for observability, not audit): `audit.seal.completed`, `audit.seal.lagging`, `audit.verify.failed`.

<!-- section:usage -->
## Usage examples

```ts
import { audit } from '@nomology/audit';

await withTenant(async (tx) => {
  const party = await tx.party.update({ where: { id }, data: { email: newEmail } });
  await audit.record(tx, {
    action: 'case.party.contact_changed',
    target: { type: 'party', id, caseId: party.caseId },
    changes: [{ field: 'email', before: { hash: h(oldEmail) }, after: { hash: h(newEmail) } }],
    subjects: [{ type: 'party', id }],
  });
});
```

```ts
// Sensitive read: issuing a signed URL to an award draft (tribunal-only)
await audit.record(tx, {
  action: 'document.download_url_issued',
  target: { type: 'document_version', id: versionId, caseId },
  meta: { visibility: 'tribunal_only', ttlSeconds: 60 },
});
```

```ts
// Denial recorded by the authz package (callers do not do this themselves)
await audit.record(tx, { action: 'authz.denied', outcome: 'denied',
  target: { type: 'case', id: caseId }, policy: { id: 'case.award.view', version: '2026.10.3' } });
```

<!-- section:tenant -->
## Tenant context

- Tenant, actor (`user`, `service`, `support`, `api_client`), `onBehalfOf` (impersonation or support access), region, request ID and trace ID are taken from `@nomology/tenant-context`; callers cannot set them. `record()` without context throws `TenantContextMissingError`.
- Events are written to `audit.audit_event`, a tenant-owned table with forced RLS ([[PKG-audit-log-schema#tenancy]]); a tenant can only ever read its own events through `search` and `exportEvents`.
- Support and impersonation actions are written to the **tenant's** audit stream with `actor.type = 'support'`, so the tenant sees them ([[PKG-support-access-and-impersonation]]).
- Platform-level actions with no tenant go to `audit.platform_audit_event` (no tenant RLS; readable only by the platform security role). Events that concern a specific tenant (provisioning, suspension, break-glass into a tenant) are written to both.
- Users who work in two tenants (for example counsel appearing before two institutions) generate separate events in each tenant; there is no cross-tenant view of a person's activity, except platform security investigations through the privileged path, which itself is audited.

<!-- section:config -->
## Configuration

| Setting | Default (proposed) | Level | Who changes |
|---|---|---|---|
| Hot retention in Postgres | 13 months | Platform | Platform engineering |
| Total retention | Per [[PKG-retention-and-deletion-schedule]]: case-linked events follow the case record (assumption: at least 7 years after case closure); security events at least 1 year, and 180 days kept in India for tenants in the India region per CERT-In [R1] | Platform, extendable per tenant contract | DPO / legal |
| Seal interval | 60 s | Platform | Platform engineering |
| Anchor interval | Daily digest per region to WORM bucket | Platform | Security |
| Export size limit | 5 million events per export job | Platform | — |
| Tenant extension | Tenants may extend (never shorten) retention by contract | Tenant setting `audit.retentionYears` (locked to ≥ platform minimum) | Tenant admin with platform approval |

Assumption: retention periods above are proposals to be confirmed by legal per tenant type; DPDP Rules 2025 contain log-retention duties that legal must map ([R2]).

<!-- section:adapters -->
## Providers and extension points

- **Anchor store**: `AnchorStore` interface with `S3ObjectLockAnchorStore` (bucket with Object Lock in compliance mode, so no user including the root account can delete or overwrite during retention [R3]) and `AzureImmutableBlobAnchorStore` for Azure deployments.
- **SIEM forwarder**: security-category events are also published to the regional OpenTelemetry log pipeline ([[OBS-security-events]]); the forwarder is a BullMQ consumer of the outbox, so audit writes never wait on the SIEM.
- **Archive**: partitions older than the hot window are exported per tenant to the regional archive bucket as JSONL plus a manifest of hashes, before the partition is detached.

<!-- section:errors -->
## Error model

| Error | Retryable | Caller action |
|---|---|---|
| `UnknownAuditActionError` | No | Register the action; caught in tests |
| `AuditWriteError` | Same as the surrounding transaction | Transaction rolls back; the change does not happen without its audit record |
| `TenantContextMissingError` | No | Fix entry point |
| Meta validation failure | No | Fix caller; thrown as `AuditWriteError` with details in dev only |
| Seal job lagging | — | Not a caller error; alert `audit.seal.lagging` |

<!-- section:nfr -->
## Performance and limits

- `record()` adds p95 ≤ 3 ms to a transaction (one INSERT, no locks on shared rows — chaining happens in the sealer).
- Write volume (proposed sizing): up to 200 events/s per region sustained, 2,000/s burst (bulk imports for a SEBI ODR tenant).
- Sealing lag p99 ≤ 2 minutes; alert at 10 minutes.
- Tenant search over 13 months: p95 ≤ 2 s for filtered queries (by case, actor, action, time range).
- Export: 1 million events in ≤ 10 minutes.

<!-- section:versioning -->
## Versioning and compatibility

Semver for the API. The event envelope has `schema_version`; new optional fields are minor, removed or renamed fields require a new envelope version, and verification code keeps every past canonicalisation so old batches always verify. Actions are never renamed; a replaced action is marked deprecated in the catalogue.

<!-- section:testing -->
## Test contract

- Contract test for each package that declares audited operations: performing the operation inserts exactly the expected action with the expected target (runs in each package's CI).
- Atomicity: a forced failure after `record()` rolls back both change and event; a forced audit failure rolls back the change.
- Immutability: `nomo_app` and `nomo_worker` UPDATE / DELETE / TRUNCATE on `audit_event` fails with permission errors.
- Tamper detection: modifying a stored event (as `nomo_migrator` in a test database) makes `verifyRange` fail and reports the batch.
- Isolation: tenant A cannot search, export or verify tenant B's events.
- Redaction: fields tagged personal never appear as `value` in `changes`.

<!-- section:questions -->
## Open questions

- [ ] Confirm retention per tenant type (arbitral institution, SEBI ODR institution, CORD) and whether institution rules require audit records to follow the case file. Owner: legal.
- [ ] Do tenants want the anchor digest published to them (for example a monthly signed digest email) so they can verify independently? Owner: product.
- [ ] Should failed sign-in attempts for unknown users be stored in tenant audit or only in security telemetry? Proposed: security telemetry only (no tenant user exists).
- [ ] Is 60-second sealing acceptable to security, given unsealed events are protected only by grants and triggers until sealed?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Tenant and actor come only from context. Events are stored in a forced-RLS tenant table, search and export run inside `withTenant`, and support actions land in the tenant's own stream. Platform-level events are in a separate table without tenant access. Export files are written under the tenant's storage prefix and delivered as signed URLs checked against `audit.export` permission.

<!-- check:data-protection -->
### Personal data handling

The API has no field for document content; `changes` stores hashes for personal fields and values only for fields tagged non-personal. `subjects` lets rights-request handling find events about a person without scanning content. Because the audit trail is evidence, erasure requests are answered by keeping events (legal-record exemption, to be confirmed by legal) while the referenced personal data is erased or anonymised in the domain tables; the hashes left in audit cannot be reversed without the original value.

<!-- check:residency -->
### Region awareness

Events live in the regional database and are archived and anchored to buckets in the same region. The SIEM forwarder uses the regional collector; any SIEM vendor receiving India-region events must be listed in [[SEC-vendor-sub-processor-management]], and CERT-In's requirement to keep logs within Indian jurisdiction for 180 days [R1] is met by the in-region database copy regardless of the SIEM.

<!-- check:audit -->
### Audit events

This package is the audit mechanism: writes happen in the same transaction as the change (no outbox gap), the app role has INSERT and SELECT only, a trigger blocks UPDATE and DELETE even for the owner outside the retention job, events are sealed into hash-chained Merkle batches every 60 s and daily digests are anchored to WORM storage in the region. Sensitive reads (signed URLs for tribunal-only documents, KYC files, award drafts) are audited, not only writes.

<!-- check:observability -->
### Observability

Metrics: `audit.events.written` (category, outcome), `audit.seal.lag_seconds` gauge, `audit.verify.failures`, export durations. Alerts: seal lag > 10 min, any verify failure (security incident path in [[SEC-security-incident-response-and]]). Logs never include `changes` or `meta` values.

<!-- check:resilience -->
### Failure behaviour

`record()` is a plain INSERT in the caller's transaction, so it shares the caller's retry semantics (Temporal or BullMQ retries the whole Activity; the idempotent domain operation decides whether a second event is written). The sealer is idempotent (re-running a batch recomputes the same root) and resumes from the last sealed horizon. If the anchor store is unavailable, sealing continues and anchoring catches up; an alert fires after 24 h without an anchor.

<!-- check:testing -->
### Testing

See the test contract: per-package audited-operation contract tests, atomicity, immutability grants, tamper detection via `verifyRange`, tenant isolation of search and export, and redaction. These run on every PR touching `packages/audit` or any package that registers audit actions.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "The Directions require service providers to maintain logs of ICT systems securely for a rolling period of 180 days within Indian jurisdiction.",
    "id": "R1",
    "issued": "2022-04-28",
    "issuer": "CERT-In (Ministry of Electronics and IT, India)",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Directions under section 70B(6) of the IT Act, 2000",
    "title": "CERT-In Directions relating to information security practices, procedure, prevention, response and reporting of cyber incidents",
    "url": "https://www.cert-in.org.in/Directions70B.jsp"
  },
  {
    "id": "R2",
    "issuer": "Government of India (MeitY)",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Digital Personal Data Protection Rules, 2025",
    "title": "Digital Personal Data Protection Rules, 2025 (Gazette notification)",
    "url": "https://www.meity.gov.in/static/uploads/2025/11/53450e6e5dc0bfa85ebd78686cadad39.pdf"
  },
  {
    "excerpt": "In compliance mode, a protected object version cannot be overwritten or deleted by any user, including the root user in the AWS account.",
    "id": "R3",
    "kind": "vendor",
    "title": "Amazon S3 User Guide: Locking objects with Object Lock",
    "url": "https://docs.aws.amazon.com/AmazonS3/latest/dev/object-lock.html",
    "vendor": "Amazon Web Services"
  }
]
```

<!-- end -->
