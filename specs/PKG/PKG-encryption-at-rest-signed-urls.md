---
id: "PKG-encryption-at-rest-signed-urls"
title: "Encryption, signed URLs and malware scanning"
parent: "PKG-storage"
order: 2
type: "feature"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "Encryption at rest per region, short-lived signed URLs checked at issue time, malware scanning before any file is viewable; retention is applied by the Data retention and legal hold package"
links: []
rev: 3
syncHash: "e9364238eee91da1"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.3.2 Encryption, signed URLs and malware scanning

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Encryption at rest per region, short-lived signed URLs checked at issue time, malware scanning before any file is viewable; retention is applied by the Data retention and legal hold package

<!-- section:purpose -->
## Purpose and scope

Makes stored files safe to keep and safe to share: every object is encrypted at rest with a regional KMS key; nobody can view or download an uploaded file until a malware scan has cleared it; and downloads and uploads happen through short-lived signed URLs that are issued only after an authorisation check at the moment of issue. Retention and holds are applied by [[PKG-data-retention-legal-hold-and]] using the lock APIs here.

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use case |
|---|---|
| Upload dropzone ([[PKG-file-upload-dropzone]]) | Request signed upload URLs, poll scan status, show "scanning" / "blocked" states |
| Document viewer ([[APP-document-viewer-and-sandbox]]) | Request a 60-second view URL on the sandbox origin for a scanned-clean version |
| Public API documents ([[INT-public-api-documents-and-filings]]) | Signed download URLs for API clients, same checks |
| eBundling and AI pipelines | Read clean objects only; never quarantined ones |
| Retention | Place and release legal holds on objects |

<!-- section:api -->
## Public API

```ts
// packages/storage/src/access.ts (server-only)
export type ScanStatus = 'pending' | 'clean' | 'infected' | 'unscannable' | 'error';

/** Upload: returns per-part signed PUT URLs into the quarantine area. */
export function issueUploadUrl(tx: TenantTx, p: {
  purpose: 'case_document' | 'transcript' | 'branding_asset';
  caseId?: string; contentType: string; sizeBytes: number; sha256: string; fileName: string;
}): Promise<{ uploadId: string; parts: { partNumber: number; url: string }[]; expiresAt: Date }>;   // URL TTL 15 min

/** Download / view: authz checked here, at issue time. */
export function issueDownloadUrl(tx: TenantTx, p: {
  objectId: string; disposition: 'inline-sandbox' | 'attachment';
  ttlSeconds?: number;               // default 60, max 300
}): Promise<{ url: string; expiresAt: Date }>;

export function scanStatus(tx: TenantTx, objectId: string): Promise<{ status: ScanStatus; scannedAt?: Date; engine?: string }>;
export function onScanResult(handler: (evt: ScanResultEvent) => Promise<void>): void;   // domain hook: e.g. mark document version available

export function placeLegalHold(ref: StoredObjectRef, holdId: string): Promise<void>;
export function releaseLegalHold(ref: StoredObjectRef, holdId: string): Promise<void>;  // only when no other hold remains

export class NotScannedError extends Error {}      // download requested before 'clean'
export class BlockedFileError extends Error {}     // infected or unscannable
```

Upload lifecycle (`stored_object.scan_status` and `availability`):

```
issueUploadUrl → client PUT to quarantine bucket → completeUpload
  → BullMQ job scan.file (regional scanner) → clean: copy to class bucket, availability = 'available', emit storage.scan.clean
                                            → infected / unscannable: availability = 'blocked', notify uploader + case manager, keep in quarantine 30 days then delete
```

<!-- section:usage -->
## Usage examples

```ts
// Server Action behind the viewer
export async function getViewUrl(documentVersionId: string) {
  return withTenant(async (tx) => {
    const v = await documents.loadVersion(tx, documentVersionId);          // RLS
    await authz.assert(tx, 'document.download_url', { type: 'document_version', id: v.id });
    return issueDownloadUrl(tx, { objectId: v.objectId, disposition: 'inline-sandbox' });
    // throws NotScannedError -> UI shows "Still checking this file"
  });
}
```

<!-- section:tenant -->
## Tenant context

`issueUploadUrl` and `issueDownloadUrl` take a `TenantTx`, load the `stored_object` row under RLS (so only the current tenant's objects are visible) and build URLs only from that row's key. `issueDownloadUrl` calls `authz.assert` itself as a second check, even if the caller already did, so a forgotten check in a consumer cannot leak a file. Scanner jobs carry tenant context and write results through `withTenant`. Quarantine and class buckets are regional; keys are tenant-prefixed ([[PKG-object-storage-abstraction-s3#tenant]]).

<!-- section:config -->
## Configuration

| Setting | Default (proposed) | Level |
|---|---|---|
| Download URL TTL | 60 s (max 300 s) | Platform; tenant can lower |
| Upload URL TTL | 15 min per part | Platform |
| Encryption | SSE-KMS with regional customer-managed key per class (S3 Bucket Keys on); Azure: customer-managed key in Key Vault | Infrastructure |
| Scanner | ClamAV-based scanning service per region, or cloud-native malware protection; engine signatures updated hourly | Infrastructure (open question) |
| Max scan size | 2 GiB documents; recordings exempt from AV but type-checked (container sniffing) | Platform |
| Encrypted / password-protected archives and PDFs | `unscannable` → blocked unless tenant setting `storage.allowUnscannableWithReview` lets a case manager release after review | Tenant |
| Quarantine retention for blocked files | 30 days | Platform |

<!-- section:adapters -->
## Providers and extension points

`MalwareScanner` interface `{ scan(stream, meta): Promise<{ verdict: 'clean'|'infected'|'unscannable'; signature?: string; engine: string; engineVersion: string }> }` with a ClamAV daemon adapter and a cloud-provider adapter. URL signers: S3 presigned URLs (SigV4, `X-Amz-Expires`), Azure user-delegation SAS (never account-key SAS). Sandbox origin: download URLs with `inline-sandbox` are served through the viewer origin defined in [[APP-document-viewer-and-sandbox]] rather than the raw bucket host, so tenant app cookies never accompany file content.

<!-- section:errors -->
## Error model

| Error | Retryable | Caller action |
|---|---|---|
| `NotScannedError` | Yes, after scan completes | Poll `scanStatus` or subscribe to `storage.scan.clean` |
| `BlockedFileError` | No | Show blocked state; offer re-upload |
| `NotFoundOrDeniedError` (from authz) | No | 404 |
| Scanner unavailable | Job retried with backoff (BullMQ); after 1 h `scan_status = error` and alert | — |

<!-- section:nfr -->
## Performance and limits

- URL issue p95 ≤ 50 ms (one RLS query, one policy decision, local signing).
- Scan: p95 ≤ 60 s for files ≤ 50 MB after upload completion; queue depth alert at 500 pending.
- Revocation: because URLs live 60 s, removing someone's access stops new downloads at once and in-flight URLs expire within a minute.

<!-- section:versioning -->
## Versioning and compatibility

Semver. Changing default TTLs is a minor change announced to consumers; changing scan gating (for example allowing view before scan) is a major, security-reviewed change.

<!-- section:testing -->
## Test contract

- Upload of the EICAR test file ends `infected` and is never downloadable; encrypted ZIP ends `unscannable` and blocked.
- `issueDownloadUrl` for another tenant's object ID → not found; for a tribunal-only version as a party → denied; before scan → `NotScannedError`.
- URL expires after TTL (integration test with LocalStack and real S3 nightly).
- Bucket policy test: unauthenticated GET and non-TLS requests denied.

<!-- section:questions -->
## Open questions

- [ ] Scanner choice per region (self-hosted ClamAV vs cloud-native malware scanning) — cost, detection quality, Azure parity. Owner: security.
- [ ] Should downloads of `attachment` disposition be watermarked with the user's name and time for tribunal-only material?
- [ ] Per-tenant KMS keys for tenants that require crypto-shredding of files on offboarding, vs deleting objects. Proposed: per-region keys plus deletion; per-tenant keys on request.

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

URLs are issued only from RLS-visible rows plus an internal `authz.assert`, so a caller cannot obtain another tenant's object even by ID. Keys are tenant-prefixed; scan jobs carry tenant context.

<!-- check:security -->
### Security of the API surface

Nothing is viewable before a clean scan; infected and unscannable files are blocked. URLs are short-lived (60 s), signed per request, issued after an authorisation check at issue time; inline viewing is on a separate sandbox origin. Azure uses user-delegation SAS only.

<!-- check:data-protection -->
### Personal data handling

Objects are encrypted at rest with regional KMS keys; object metadata contains no personal data (original file names are kept in the database as confidential metadata). Retention, erasure and holds are applied through this package by the retention package.

<!-- check:audit -->
### Audit events

Audited: download URL issue for tribunal-only, institution-internal and KYC objects (reads), scan verdicts `infected` and `unscannable`, release of an unscannable file by a case manager, legal hold place and release.

<!-- check:observability -->
### Observability

Metrics: scan duration and verdict counts per region, pending queue depth, URL issue rate by disposition, `NotScannedError` rate. No file names or content in telemetry.

<!-- check:resilience -->
### Failure behaviour

Scanning is asynchronous on BullMQ with retries; if the scanner is down, files stay `pending` (fail closed) and an alert fires after 15 minutes of backlog growth. URL issue has no remote dependency except the database.

<!-- end -->
