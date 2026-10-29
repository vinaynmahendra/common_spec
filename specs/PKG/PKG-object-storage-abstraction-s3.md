---
id: "PKG-object-storage-abstraction-s3"
title: "Object storage abstraction (S3 / GCS / Azure Blob)"
parent: "PKG-storage"
order: 1
type: "feature"
template: "package"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 3
syncHash: "d5f13f881456d0db"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.3.1 Object storage abstraction (S3 / GCS / Azure Blob)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

A provider-neutral object storage API used by every app and worker, with implementations for Amazon S3 and Azure Blob Storage (Google Cloud Storage optional, see questions). It fixes the key layout, bucket-per-region-and-class mapping, multipart and resumable uploads, streaming reads, server-side copy, object metadata and lifecycle hooks so that domain code never touches provider SDKs.

**Does not:** issue signed URLs or scan files (sibling [[PKG-encryption-at-rest-signed-urls]]); decide access ([[PKG-authorization]]); hold document metadata ([[DOM-documents-schema]]).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Call |
|---|---|
| Upload flow (portal) | `createUpload` → client PUTs parts → `completeUpload` |
| eBundling Activities | `getObjectStream` for sources, `putObject` for bundle output, `copyObject` for re-issue |
| Recording ingest Activity | `putObject` streaming from the video provider with checksum |
| Document generation Activity | `putObject` for generated PDFs (immutable) |
| Retention deletion workflow | `deleteObject` (all versions) after hold checks |
| Audit archive and anchor jobs | `putObject` to WORM buckets with retention |

<!-- section:api -->
## Public API

```ts
// packages/storage/src/objects.ts  (server-only)
export type ObjectClass = 'case_document' | 'recording' | 'transcript' | 'generated_document' | 'bundle'
  | 'export' | 'branding_asset' | 'audit_archive' | 'audit_anchor' | 'temp_upload';

export interface StoredObjectRef { id: string; class: ObjectClass; key: string; versionId?: string }

/** The only key builder; reads tenant and region from context. */
export function objectKey(cls: ObjectClass, objectId?: string): { key: string; bucket: string };

export function putObject(p: {
  class: ObjectClass; body: Uint8Array | NodeJS.ReadableStream; contentType: string;
  sha256: string;                    // required; verified by the provider (x-amz-checksum-sha256 / Content-MD5 equivalent)
  sizeBytes: number; metadata?: Record<string, string>;   // ASCII, ≤ 2 KB, no personal data
  retainUntil?: Date;                // WORM classes only
  idempotencyKey: string;            // same key + same hash => same object, no duplicate
}): Promise<StoredObjectRef>;

export function createUpload(p: { class: 'temp_upload'; contentType: string; sizeBytes: number; sha256?: string;
  fileName: string /* sanitised, stored as metadata only */ }): Promise<{ uploadId: string; object: StoredObjectRef; partSize: number; parts: number }>;
export function completeUpload(p: { uploadId: string; parts: { partNumber: number; etag: string }[] }): Promise<StoredObjectRef>;
export function abortUpload(uploadId: string): Promise<void>;

export function getObjectStream(ref: StoredObjectRef, range?: { start: number; end: number }): Promise<NodeJS.ReadableStream>;
export function headObject(ref: StoredObjectRef): Promise<{ sizeBytes: number; sha256: string; contentType: string; lastModified: Date }>;
export function copyObject(from: StoredObjectRef, toClass: ObjectClass): Promise<StoredObjectRef>; // server-side, same region only
export function deleteObject(ref: StoredObjectRef, p: { allVersions: true; reason: DeletionReason; holdCheckToken: HoldCheckToken }): Promise<void>;

export class ObjectNotFoundError extends Error {}
export class ChecksumMismatchError extends Error {}
export class StorageUnavailableError extends Error {}     // retryable
export class RegionMismatchError extends Error {}
export class LegalHoldActiveError extends Error {}
```

`deleteObject` requires a `HoldCheckToken` issued by [[PKG-data-retention-legal-hold-and]] after it has confirmed no hold covers the object, so no code path can delete held material by calling storage directly.

<!-- section:usage -->
## Usage examples

```ts
// Activity: write a generated procedural order as an immutable object
const ref = await putObject({
  class: 'generated_document', body: pdfBytes, contentType: 'application/pdf',
  sha256: sha256Hex(pdfBytes), sizeBytes: pdfBytes.length,
  idempotencyKey: `${tenantId}:order:${orderId}:v${version}`,
});
await withTenant((tx) => tx.storedObject.create({ data: { id: ref.id, class: ref.class, key: ref.key, sha256, sizeBytes } }));
```

```ts
// Retention workflow: delete only with a hold-check token
const token = await retention.checkHolds({ type: 'stored_object', id: ref.id });  // throws LegalHoldActiveError
await deleteObject(ref, { allVersions: true, reason: 'retention_expired', holdCheckToken: token });
```

<!-- section:tenant -->
## Tenant context

- `objectKey` builds `t/{tenantId}/{class}/{yyyy}/{mm}/{uuidv7}` from `@nomology/tenant-context`; there is no API that accepts a raw key from a caller. Reads and deletes take a `StoredObjectRef` that the caller obtained from a `stored_object` row loaded under RLS, and the package re-checks that the key prefix matches the context tenant (`TenantMismatchError` otherwise).
- Buckets per region and class, for example `nomology-prod-in-case-documents`, `nomology-prod-in-recordings`, `nomology-prod-in-audit-anchor` (Object Lock). Bucket policies allow only the region's application and worker roles, block public access, and require TLS.
- Optional per-tenant isolation for tenants that require it by contract: dedicated bucket per tenant per class (configured in the tenant's storage profile); the key layout is unchanged.
- Background Activities receive tenant context from the Temporal interceptor; BullMQ scan jobs carry the signed context envelope ([[PKG-data-access#tenant]]).

<!-- section:config -->
## Configuration

| Setting | Default (proposed) | Where |
|---|---|---|
| Provider | `s3` (AWS regions), `azure_blob` (Azure deployments) | Env per region |
| Bucket / container map per class | Terraform outputs injected as env | [[INF-cloud-and-iac]] |
| Part size | 16 MiB; max object 50 GiB (recordings), 2 GiB (documents) | Code per class |
| Upload expiry for incomplete multipart | 24 h (lifecycle rule) | Bucket config |
| `temp_upload` lifecycle | delete after 7 days if not promoted | Bucket config |
| Versioning | On for all classes; required for Object Lock classes | Bucket config |
| Per-tenant dedicated bucket | Off | Tenant storage profile (platform admin) |

<!-- section:adapters -->
## Providers and extension points

`ObjectStoreAdapter` interface: `put`, `createMultipart`, `presignPart` (used by the sibling), `completeMultipart`, `abortMultipart`, `getStream`, `head`, `copy`, `deleteAllVersions`, `setRetention`, `setLegalHold`. Implementations: `S3Adapter` (AWS SDK v3, checksum SHA-256), `AzureBlobAdapter` (block blobs, immutability policies for WORM classes, legal hold tags), `GcsAdapter` (optional). Each adapter passes the same contract suite against LocalStack, Azurite and real cloud accounts in nightly runs.

<!-- section:errors -->
## Error model

| Error | Retryable | Caller action |
|---|---|---|
| `StorageUnavailableError` (5xx, throttling, timeouts) | Yes — leave to Temporal / BullMQ retry policy | — |
| `ChecksumMismatchError` | No (retry upload from source) | Re-read source; alert if repeated |
| `ObjectNotFoundError` | No | Treat as data integrity issue if the DB row exists |
| `RegionMismatchError`, `TenantMismatchError` | No | Bug; security event |
| `LegalHoldActiveError` | No | Skip deletion; record in retention run |

<!-- section:nfr -->
## Performance and limits

- `putObject` for 10 MB p95 ≤ 1 s in-region; streaming throughput ≥ 50 MB/s per worker.
- `headObject` p95 ≤ 50 ms.
- Timeouts: 5 s connect, 60 s per part, overall bounded by the Activity start-to-close timeout.
- No buffering of whole files in memory above 32 MB; streams only.

<!-- section:versioning -->
## Versioning and compatibility

Semver. `ObjectClass` additions are minor; changing a class's bucket or key layout is major and needs a migration plan (copy plus dual-read). Adapter interface changes are major.

<!-- section:testing -->
## Test contract

Contract suite per adapter (LocalStack S3, Azurite); tenant prefix enforcement tests (a ref from tenant A used in tenant B context fails); idempotent `putObject` (same key twice → one object); delete without hold token impossible (type-level) and with an active hold fails; multipart abort cleans up; region mismatch refused at start-up.

<!-- section:questions -->
## Open questions

- [ ] Keep GCS adapter in scope? Proposed: interface only until a client requires it.
- [ ] Which tenants need dedicated buckets by contract? Affects Terraform per tenant.
- [ ] Do we deduplicate identical files across a tenant (content-addressed) to save storage for re-filed exhibits? Proposed: no — simpler deletion and holds.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Keys are generated from context only; refs come from RLS-protected rows and their prefix is re-checked against the context tenant; bucket policies admit only regional app roles. Cross-tenant use of a ref raises `TenantMismatchError` and a security event.

<!-- check:security -->
### Security of the API surface

No caller-supplied keys or paths; file names are metadata only after sanitisation ([[PKG-input-sanitisation-csrf-rate]]); public access blocked on all buckets; TLS required by bucket policy; IAM roles per region with access to that region's buckets only; delete requires a retention hold token.

<!-- check:residency -->
### Region awareness

Buckets exist per region and per class; the adapter validates the bucket region at start-up and refuses mismatches; `copyObject` works only within a region. Moving a tenant between regions is an explicit migration ([[MT-data-residency-2]]), not a storage feature.

<!-- check:audit -->
### Audit events

Object creation and deletion are audited by the calling domain operation (document version created, retention deletion); the package itself emits `storage.object.deleted` audit events for deletions, including the hold-check token ID.

<!-- check:resilience -->
### Failure behaviour

`putObject` is idempotent by key and hash; multipart uploads can be resumed or aborted; transient provider errors are surfaced as retryable and retried by Temporal or BullMQ, not inside the package (one SDK-level retry for connection resets only).

<!-- check:testing -->
### Testing

Contract tests per adapter on LocalStack and Azurite in CI, nightly against real cloud accounts per region; tenant-prefix and hold-token tests on every change.

<!-- end -->
