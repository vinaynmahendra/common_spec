---
id: "APP-document-viewer-and-sandbox"
title: "Document viewer and sandbox origin"
parent: "APP-frontend-standards"
order: 4
type: "feature"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Rendering of uploaded PDFs and exhibits on a separate sandboxed origin; annotation, page-level links, large-bundle performance"
links: []
rev: 2
syncHash: "c3ca372a8ec259ba"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.4.4 Document viewer and sandbox origin

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Rendering of uploaded PDFs and exhibits on a separate sandboxed origin; annotation, page-level links, large-bundle performance

<!-- section:scope -->
## Scope, audiences and surfaces

How uploaded documents and exhibits (PDFs, images, office documents converted to PDF, and eBundles with thousands of pages) are rendered for every persona, on a **separate sandboxed origin**, with annotations, page-level links and good performance on large bundles.

- Viewer UI controls (toolbar, page navigation, zoom, search) are the component [[PKG-document-viewer-controls]]; this node covers rendering, isolation, messaging and performance.
- Storage, signed URLs and malware scanning: [[PKG-encryption-at-rest-signed-urls]].
- Bundle assembly and pagination: [[DOM-ebundling]]. Accessibility of documents: [[DOM-accessible-documents-and]].

Hosts: per region, a sandbox origin on a **separate registrable domain** from the app (for example `{region}.{usercontent-domain}`), so it shares no cookies and is cross-site to every tenant host.

<!-- section:routing -->
## Routes, layouts and boundaries

App side (in each group): `.../documents/[docId]` (full page) and `@modal/(.)documents/[docId]` (modal). Both render `<DocumentFrame docId=… page=…>`, which:

1. calls `*.documents.getViewUrl` (tRPC) to obtain a viewer URL on the sandbox origin with a short-lived token (5 minutes, single document, single user, bound to tenant);
2. embeds `<iframe src="https://{sandbox}/v/{token}#page=45" sandbox="allow-scripts allow-downloads" allow="fullscreen" referrerpolicy="no-referrer">` (no `allow-same-origin`, no `allow-top-navigation`, no `allow-forms`);
3. talks to the viewer by `postMessage` with origin checks on both sides.

Sandbox origin (static viewer app, served from regional storage behind the CDN, no Next.js):

```text
https://{sandbox}/v/{token}         # viewer shell (PDF.js-based), token in path
https://{sandbox}/f/{token}/{part}  # byte-range PDF stream from object storage (signed, 5 min)
```
Deep links: `#page=45` for documents; bundles use bundle page numbers (`#bp=1203`) mapped by the viewer to document and page.

<!-- section:rendering -->
## Rendering and caching strategy

- PDFs render with PDF.js in the sandboxed iframe, with range requests and lazy page rendering (only visible pages plus two ahead and behind), canvas plus text layer for search and selection.
- Images are converted to PDF on upload (or rendered as `<img>` in the viewer).
- Office documents and HTML exhibits are **never** rendered as live HTML; they are converted to PDF in a worker during the upload pipeline, and the original is available for download only.
- Thumbnails come from server-generated page images (WebP), not client rendering.
- No caching beyond the token lifetime: `Cache-Control: private, max-age=300` on byte-range responses, keyed by the token URL.

<!-- section:data -->
## Data fetching and mutations

| Operation | Kind | Notes |
|---|---|---|
| `*.documents.getViewUrl` | tRPC mutation | checks access to document version, audits a "document viewed" event, returns token URL |
| `*.documents.annotations.list` / `save` | tRPC | annotations stored per user (private) or shared within a role group (tribunal-only, party side) |
| `viewer → app` messages | `postMessage` | `ready`, `pageChanged {page}`, `selection {page, rects, text≤500}`, `annotationRequest`, `linkClicked {bundlePage}` |
| `app → viewer` messages | `postMessage` | `goToPage`, `setAnnotations`, `highlight`, `setTheme` |

The viewer never calls app APIs itself; annotations go through the parent app, which applies normal authorisation.

<!-- section:state -->
## Client state and URL state

Current page per document is kept in the URL hash of the parent route (`#page=45`) so links can be shared within the case. Annotations live on the server. The viewer stores nothing in the browser (no cookies or storage on the sandbox origin).

<!-- section:errors -->
## Error, loading and empty handling

| Situation | Handling |
|---|---|
| Token expired | Viewer asks parent for a fresh URL silently via `tokenExpired` message |
| File still being scanned | Parent shows "Checking file" status; viewer not loaded |
| File infected or conversion failed | Parent shows the reason and, for conversion failures, a download of the original after a warning |
| PDF damaged | Viewer shows "This document cannot be displayed" with download option; reported to secretariat queue |
| Not allowed | `getViewUrl` returns `not-found` |

<!-- section:performance -->
## Performance budgets

Targets (proposed): first page visible ≤ 1.5 s p75 on broadband for any document size; page change ≤ 200 ms; a 5,000-page eBundle opens without downloading the whole file (range requests, linearised PDFs produced by [[DOM-ebundling]]); memory ≤ 400 MB in the iframe on desktop by evicting off-screen canvases. Viewer bundle ≤ 450 KB gzip, cached immutable on the sandbox origin.

<!-- section:security -->
## Security headers and browser session

Sandbox origin response headers:
```text
Content-Security-Policy: default-src 'none'; script-src 'self'; style-src 'self';
  img-src 'self' blob: data:; connect-src 'self'; worker-src 'self' blob:; font-src 'self';
  frame-ancestors https://*.{tenant hosts in region}; base-uri 'none'; form-action 'none'
Cross-Origin-Resource-Policy: cross-origin   (viewer assets) / same-origin (file parts)
X-Content-Type-Options: nosniff
Content-Disposition: attachment            (on downloads of originals)
Referrer-Policy: no-referrer
```
- `frame-ancestors` lists this region's tenant hosts (custom domains included, regenerated on change).
- The iframe `sandbox` without `allow-same-origin` gives the viewer an opaque origin, so even script inside a malicious PDF processed by PDF.js cannot read the sandbox origin's (empty) storage or reach the app.
- PDF.js runs with `isEvalSupported: false` and JavaScript in PDFs disabled.
- `postMessage` handlers check `event.origin` and message schema (Zod) on both sides.

<!-- section:i18n -->
## Localisation hookup

Viewer UI strings are passed from the parent at load (`init` message) in the user's locale; document text is shown as-is, with `lang` set from document metadata when known.

<!-- section:theming -->
## Tenant theming hookup

Viewer chrome follows the parent's colour mode via `setTheme`; page rendering is not recoloured, but a high-contrast inversion option exists for low-vision users.

<!-- section:observability -->
## Frontend observability

Metrics: time to first page, range-request bytes per view, render failures by error class; document IDs are hashed in telemetry; views are audited server-side when tokens are issued.

<!-- section:testing -->
## Testing strategy

- Malicious-file suite: PDFs with embedded JavaScript, launch actions, XFA forms, SVG with script, polyglot files; assert no script runs in the app origin and no network calls leave the sandbox origin except allowed ones.
- Large-bundle performance test with a 5,000-page linearised PDF.
- Keyboard and screen-reader tests of viewer controls and text layer ([[PKG-document-viewer-controls]]).
- Header tests for sandbox origin per region.

<!-- section:questions -->
## Open questions

- [ ] Sandbox registrable domain per region, and whether Azure deployments use a separate one (owner: DevOps)
- [ ] Are shared annotations needed between co-counsel, or private only at first? (owner: product)
- [ ] Commercial PDF engine (better accessibility and redaction) versus PDF.js (owner: frontend lead; Decision record)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

Tokens bind tenant, user, document version and expiry; byte-range URLs are signed per token; the sandbox origin has no session and no tenant state. `frame-ancestors` restricts embedding to this region's tenant hosts.

<!-- check:data-exposure -->
### Server boundary and data exposure

Access is checked when the token is issued, inside the tenant transaction, and audited; the viewer cannot call app APIs; selections sent to the parent are capped at 500 characters.

<!-- check:browser-security -->
### Browser security posture

Separate registrable domain, iframe sandbox without same-origin, strict CSP on the sandbox origin, PDF JavaScript disabled, no live rendering of HTML or office files, `nosniff` and attachment disposition on originals.

<!-- check:capacity -->
### Rendering cost and capacity

Range requests and linearised bundles keep bytes transferred proportional to pages viewed; static viewer assets served from the CDN; the Next.js servers are not in the file path.

<!-- check:accessibility -->
### App-level accessibility mechanics

The text layer is exposed to AT; page navigation and search are keyboard operable; untagged uploaded PDFs show a notice with a request route for an accessible copy ([[APP-accessibility-feedback]]).

<!-- check:residency -->
### Region, residency and telemetry privacy

Sandbox origin, its CDN and the file bytes are in the tenant's region; CDN caches only the static viewer assets globally if the CDN is global, never file parts (which are `private`).

<!-- end -->
