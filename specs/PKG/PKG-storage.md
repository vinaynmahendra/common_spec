---
id: "PKG-storage"
title: "Storage"
parent: "PKG"
order: 3
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 3
syncHash: "a857041fe5be5a54"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 5.3 Storage

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

`@nomology/storage` is how every app and worker stores and serves files: pleadings, exhibits, eBundles, recordings, transcripts, generated orders and awards, exports and tenant branding assets. This parent node sets the shared contract; the two children specify it:
- [[PKG-object-storage-abstraction-s3]] — provider-neutral object API (S3, Azure Blob, GCS), key layout, buckets per region and object class, multipart uploads, lifecycle
- [[PKG-encryption-at-rest-signed-urls]] — encryption per region, short-lived signed URLs checked at issue time, malware scanning before anything is viewable

**Does not:** decide who may read a file (that is [[PKG-authorization]], called before any URL is issued); own document metadata, versions and hashes ([[DOM-documents-schema]]); decide how long files live ([[PKG-data-retention-legal-hold-and]] applies retention and holds through this package's delete and lock APIs); render documents ([[APP-document-viewer-and-sandbox]]).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use case |
|---|---|
| Party and counsel portal | Upload filings and exhibits (direct-to-storage signed PUT, then scan) |
| Neutral workspace | View exhibits and bundles through the sandboxed viewer; download award drafts (tribunal-only, audited) |
| eBundling pipeline ([[DOM-ebundling]]) | Read source PDFs, write bundle PDFs and indexes (Temporal Activities) |
| Hearings ([[INT-video-conferencing-for-hearings]]) | Ingest recordings from the provider; hand to transcription |
| Document generation ([[PKG-document-and-notification]]) | Store generated orders, receipts, awards as immutable versions |
| Audit and retention | Export files, archive partitions, WORM anchors |

<!-- section:api -->
## Public API

Public surface (detail in children):

```ts
export { putObject, createUpload, completeUpload, getObjectStream, headObject, deleteObject,
         copyObject, objectKey } from './objects';                 // PKG-object-storage-abstraction-s3
export { issueDownloadUrl, issueUploadUrl, scanStatus, onScanResult,
         placeLegalHold, releaseLegalHold } from './access';        // PKG-encryption-at-rest-signed-urls
export type { ObjectClass, StoredObjectRef, ScanStatus } from './types';
```

`ObjectClass`: `case_document`, `recording`, `transcript`, `generated_document`, `bundle`, `export`, `branding_asset`, `audit_archive`, `audit_anchor`, `temp_upload`. Each class maps to bucket, encryption key, retention defaults and whether scanning is required.

<!-- section:tenant -->
## Tenant context

Keys are built only by `objectKey()` from the tenant context: `t/{tenantId}/{class}/{yyyy}/{mm}/{objectId}` (object IDs are UUIDv7, never user-supplied names). Signed URLs are issued only for objects whose `stored_object` row (tenant-owned, forced RLS) is visible in the current tenant transaction, so a caller cannot obtain a URL for another tenant's key even by guessing it. Buckets are per region; there is no bucket shared across regions. Details: [[PKG-object-storage-abstraction-s3#tenant]].

<!-- section:questions -->
## Open questions

- [ ] Is GCS needed at all (no current client requires GCP)? Proposed: keep the interface, ship S3 and Azure Blob only.
- [ ] Recording storage volumes and costs per region (hearings can be many hours of video) — needed for [[INF-cloud-and-iac]] sizing.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

All object keys come from `objectKey()` with the tenant from context; signed URLs require a visible `stored_object` row under RLS plus an `authz` decision; bucket policies deny access except through the application roles. See children for the tests.

<!-- check:security -->
### Security of the API surface

No caller-supplied keys; files are not viewable until scanned clean; URLs live 60 seconds and are issued after an authorisation check; buckets block public access and require TLS.

<!-- check:residency -->
### Region awareness

Buckets, KMS keys and scanning workers exist per region; the package refuses to write to a bucket whose region tag differs from `APP_REGION`. No CDN caches private objects; signed URLs point directly at the regional bucket endpoint (or the regional viewer origin).

<!-- check:resilience -->
### Failure behaviour

Writes are idempotent by key and checksum; scanning is asynchronous with retries and fails closed; provider errors are surfaced as retryable for Temporal or BullMQ to retry.

<!-- check:testing -->
### Testing

Adapter contract suites on LocalStack and Azurite, tenant-prefix enforcement, EICAR blocking, URL expiry and hold-token tests run on every change.

<!-- end -->
