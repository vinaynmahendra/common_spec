---
id: "INT-public-api-documents-and-filings"
title: "Public API — Documents and filings"
parent: "INT-public-api-and-webhooks"
order: 3
type: "feature"
template: "api"
status: "draft"
owner: null
indicative: false
summary: "Upload, list and download filings and bundles via signed URLs; immutable versions and content hashes"
links: []
rev: 2
syncHash: "0b52484813334d9e"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 9.4.3 Public API — Documents and filings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Upload, list and download filings and bundles via signed URLs; immutable versions and content hashes

<!-- section:purpose -->
## Purpose, audience and surface

Lets external systems upload documents, make formal filings (a submission of one or more documents with a filing type and receipt), list and download documents, versions and eBundles. Files never pass through the API servers: uploads and downloads use short-lived signed URLs to regional object storage ([[PKG-object-storage-abstraction-s3]], [[PKG-encryption-at-rest-signed-urls]]). Every version is immutable and identified by its SHA-256 content hash ([[DOM-documents-schema]]).

Callers: institution systems filing on behalf of parties, counsel-firm tools, aggregators (attachments to bulk matters). Not exposed: drafts in a neutral's private workspace, tribunal-only documents, sealed documents (unless the principal is permitted), bundle assembly controls (secretariat UI only in v1).

<!-- section:resources -->
## Resources and identifiers

```
/v1/cases/{case_id}/uploads            upload sessions
/v1/uploads/{upload_id}
/v1/cases/{case_id}/filings            formal submissions
/v1/filings/{filing_id}
/v1/cases/{case_id}/documents
/v1/documents/{document_id}
    /versions/{version}                version numbers 1..n
    /versions/{version}/download
/v1/cases/{case_id}/bundles
/v1/bundles/{bundle_id}/versions/{version}/download
```
IDs: `upl_`, `fil_`, `doc_`, `bdl_` + UUIDv7. A document has versions 1..n; each version has `sha256`, `size_bytes`, `media_type`, `confidentiality` (from [[SEC-data-classification]]), `scan_status`.

<!-- section:operations -->
## Operations

| Method and path | Summary | Scope | Safe / idempotent / long-running |
|---|---|---|---|
| `POST /v1/cases/{case_id}/uploads` | Create upload session: file name, size, media type, SHA-256; returns signed PUT URL (or multipart part URLs above 100 MB) valid 15 min | `documents:write` | Idempotency-Key |
| `POST /v1/uploads/{upload_id}/complete` | Confirm upload; server verifies size and hash, starts malware scan | `documents:write` | idempotent; 202 while scanning |
| `GET /v1/uploads/{upload_id}` | Upload status: `pending_upload`, `scanning`, `available`, `rejected` | `documents:write` | safe |
| `POST /v1/cases/{case_id}/filings` | File a submission: filing type, on behalf of party, list of available uploads or existing document versions | `documents:write` | Idempotency-Key required |
| `GET /v1/cases/{case_id}/filings` | List filings | `documents:read` | safe |
| `GET /v1/filings/{filing_id}` | Filing with receipt (received_at, hashes) | `documents:read` | safe |
| `GET /v1/cases/{case_id}/documents` | List documents visible to caller | `documents:read` | safe |
| `GET /v1/documents/{document_id}` | Document with latest version metadata | `documents:read` | safe |
| `GET /v1/documents/{document_id}/versions` | All versions | `documents:read` | safe |
| `POST /v1/documents/{document_id}/versions` | Add a new version (from an upload) where the document type allows it | `documents:write` | Idempotency-Key |
| `GET /v1/documents/{document_id}/versions/{version}/download` | `303 See Other` to a signed GET URL (5 min) | `documents:read` | safe; audited |
| `GET /v1/cases/{case_id}/bundles` | List issued eBundles | `documents:read` | safe |
| `GET /v1/bundles/{bundle_id}/versions/{version}/download` | `303` to signed URL | `documents:read` | safe; audited |

<!-- section:schemas -->
## Request and response schemas

```ts
const UploadCreate = z.object({
  file_name: z.string().min(1).max(255).regex(/^[^\/\\\u0000-\u001f]+$/),
  size_bytes: z.number().int().positive().max(5 * 1024 ** 3),      // 5 GB (recordings excluded)
  media_type: z.enum(['application/pdf', 'image/png', 'image/jpeg', 'image/tiff',
     'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
     'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'audio/mpeg', 'video/mp4', 'text/plain']),
  sha256: z.string().regex(/^[a-f0-9]{64}$/),
}).strict();

const FilingCreate = z.object({
  filing_type: z.string().max(64),                 // tenant rule set: 'statement_of_claim', 'response', 'evidence', ...
  on_behalf_of_party_id: z.string(),
  items: z.array(z.object({
    upload_id: z.string().optional(), document_id: z.string().optional(), version: z.number().int().optional(),
    title: z.string().max(300), confidentiality: z.enum(['case_participants', 'tribunal_only']).default('case_participants'),
  }).strict()).min(1).max(200),
  note: z.string().max(2000).optional(),
}).strict();

const FilingReceipt = z.object({
  id: z.string(), case_id: z.string(), filing_type: z.string(), status: z.enum(['received', 'accepted', 'rejected']),
  received_at: z.string().datetime(),              // our clock, legal timestamp
  deadline_id: z.string().nullable(), on_time: z.boolean().nullable(),
  items: z.array(z.object({ document_id: z.string(), version: z.number(), sha256: z.string(), size_bytes: z.number() })),
});
```

<!-- section:errors -->
## Error model

RFC 9457 [R1]. Family-specific types:

| Problem type | Status | When | Retryable |
|---|---|---|---|
| `upload-hash-mismatch` | 422 | Stored object hash differs from declared `sha256` | No; re-upload |
| `upload-expired` | 410 | Signed URL window passed before complete | No; new session |
| `upload-not-available` | 409 | Filing references an upload still scanning or rejected | Yes after scan |
| `file-rejected-malware` | 422 | Scan found malware; file deleted | No |
| `media-type-not-allowed` | 422 | Detected type differs from declared or not allowed for filing type | No |
| `filing-window-closed` | 409 | Rule set forbids filing in current stage (late filings are allowed but flagged `on_time=false` unless the rule set blocks them) | No |
| `document-version-immutable` | 409 | Attempt to replace a version | No |
| plus the shared types (validation, not-found, idempotency, rate-limited) | | | |

<!-- section:auth -->
## Authentication, scopes and permissions

Scopes `documents:read`, `documents:write`. Object checks: the principal must be allowed to file for `on_behalf_of_party_id` (secretariat role, or representative of that party), and to read each document under its confidentiality tier ([[PKG-rbac-abac-case-level-party]]). Signed URLs are issued only after that check, are single-object, short-lived (PUT 15 min, GET 5 min) and bound to region bucket and key; they carry no reusable credential.

<!-- section:tenancy -->
## Tenancy and region routing

The tenant is taken only from the credential (API key or OAuth token), which is bound to one tenant and one region ([[INT-public-api-and-webhooks#auth]]). The auth middleware opens the request transaction and sets `app.tenant_id` through the Prisma extension ([[MT-prisma-client-extension-wraps]]); forced RLS ([[MT-rls-enabled-and-forced-on]]) is the final layer under the object-level policy checks. No path, query or body field can select a tenant; `tenant_id` is not accepted in any write schema (`additionalProperties: false`). A credential used against another region's base URL gets `421` problem `wrong-region`. A suspended tenant gets read access and the protected due-process actions only; other writes return `403` problem `tenant-suspended-readonly`. Unknown and forbidden IDs both return the same `404 not-found`.

Object keys are `{region}/{tenantId}/{caseId}/{documentId}/{version}`; the upload session records tenant and case, so `complete` and filings re-check that the upload belongs to the same tenant, case and client.

<!-- section:pagination -->
## Pagination, filtering and sorting

Cursor pagination as in other families; documents filterable by `filing_id`, `document_type`, `updated_after`, `confidentiality`; filings by `filing_type`, `received_after`. Index `(tenant_id, case_id, created_at DESC)`.

<!-- section:idempotency -->
## Idempotency, concurrency and long-running operations

Create upload and filing require `Idempotency-Key` [R2]; a retried filing returns the same receipt and `received_at`, never a second filing. `complete` is naturally idempotent. Scanning is asynchronous: `complete` returns `202` with the upload resource; clients poll `GET /v1/uploads/{id}` or wait for `document.version_available` / `document.rejected`.

<!-- section:events -->
## Webhooks and events

`filing.received`, `document.version_available`, `document.rejected`, `bundle.issued` ([[INT-webhook-event-catalogue]]).

<!-- section:limits -->
## Rate limits and quotas

Max 5 GB per file via multipart; 20 concurrent upload sessions per client; 200 items per filing; downloads 300 per minute per client (counts signed URL issuance). Upload bandwidth is limited by object storage, not the API.

<!-- section:versioning -->
## Versioning, compatibility and deprecation

Additive changes only in `/v1`. New media types and filing types are configuration (rule sets), not contract changes; clients must tolerate unknown `filing_type` values.

<!-- section:examples -->
## Worked examples

1. `POST /v1/cases/case_01JB.../uploads` with `sha256` → `201 { "id": "upl_...", "put_url": "https://...s3.ap-south-1...", "expires_at": "..." }`
2. `PUT {put_url}` with the file bytes.
3. `POST /v1/uploads/upl_.../complete` → `202 { "status": "scanning" }`; later `document.version_available`.
4. `POST /v1/cases/case_01JB.../filings` with `Idempotency-Key` → `201` receipt with `received_at` and hashes.

Failure: step 3 returns `422 upload-hash-mismatch` because the file was truncated; the client starts a new upload session.

<!-- section:questions -->
## Open questions

- [ ] Is `received_at` the legal filing time, or the time the upload completed (matters for deadlines at midnight)? Proposed: `received_at` of the filing call, after all items are available; legal to confirm per rule set.
- [ ] Maximum file size for parties versus institutions; recordings via API at all?
- [ ] Should clients be able to request bundle generation through the API in a later version?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Object-level authorization and tenant isolation

Signed URLs are issued per object after the policy check and are bound to tenant-prefixed keys; upload sessions are re-checked for tenant, case and client on completion and filing; confidentiality tiers are applied to every list and download.

<!-- check:security -->
### Attack surface and abuse resistance

Declared hash and size verified server-side; content type detected and checked; malware scan before availability; file names sanitised; short-lived signed URLs; uploads go directly to storage so API servers never parse file bytes.

<!-- check:reliability -->
### Retry safety and consistency

Idempotent filings return the same receipt; filings reference only scanned, available uploads; receipts carry our clock's `received_at` and hashes.

<!-- check:privacy -->
### Personal data and residency in the contract

Document content never appears in URLs, events or logs; tribunal-only and sealed documents are excluded unless the principal is permitted.

<!-- check:audit -->
### Attribution and legal evidence

Filings are recorded with content hashes, `received_at`, client, principal and request ID; every download (signed URL issuance) is audited as a sensitive read.

<!-- citations -->
## Citations

```json
[
  {
    "body": "IETF",
    "excerpt": "Defines the application/problem+json object with type, title, status, detail and instance members.",
    "id": "R1",
    "ident": "RFC 9457",
    "kind": "standard",
    "title": "Problem Details for HTTP APIs",
    "url": "https://datatracker.ietf.org/doc/html/rfc9457"
  },
  {
    "body": "IETF (Internet-Draft)",
    "excerpt": "Defines an Idempotency-Key request header so that clients can safely retry non-idempotent requests such as POST.",
    "id": "R2",
    "ident": "draft-ietf-httpapi-idempotency-key-header-06",
    "kind": "standard",
    "title": "The Idempotency-Key HTTP Header Field",
    "url": "https://datatracker.ietf.org/doc/html/draft-ietf-httpapi-idempotency-key-header-06"
  }
]
```

<!-- end -->
