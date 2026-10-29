---
id: "PKG-file-upload-dropzone"
title: "File upload dropzone"
parent: "PKG-ui-design-system"
order: 6
type: "feature"
template: "component"
status: "draft"
owner: null
indicative: false
summary: "Multi-file upload with progress, virus-scan status, retry and keyboard alternative to drag and drop"
links: []
rev: 2
syncHash: "3c3d5ad35824dc9d"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.6 File upload dropzone

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Multi-file upload with progress, virus-scan status, retry and keyboard alternative to drag and drop

<!-- section:purpose -->
## Purpose and when to use

`FileDropzone` uploads one or many files (pleadings, exhibits, evidence, audio for transcription, tenant logos) with per-file progress, malware-scan status, retry and removal. It offers a "Choose files" button so drag and drop is never required (WCAG 2.5.7) [R1]. Upload goes direct to object storage with signed URLs from [[PKG-encryption-at-rest-signed-urls]]; documents are not viewable until the scan passes.

<!-- section:anatomy -->
## Anatomy

| Part | Required | Element |
|---|---|---|
| Label and hint | Yes | `<label>` for the hidden `<input type="file">`; hint lists accepted types and limits |
| Choose files button | Yes | `Button` that opens the native picker |
| Drop area | No (enhancement) | `<div>` drop target, not focusable itself |
| File list | When files exist | `<ul>`; each item has name, size, status text, progress bar (`<progress>` with label), Retry / Remove `IconButton`s |
| Status region | Yes | Polite live region summarising changes |

<!-- section:variants -->
## Variants and sizes

`single` (logo, signature page), `multiple` (exhibits; default), `ordered` (adds move up / move down buttons, for bundle order; no drag-only ordering).

<!-- section:states -->
## States

Per file: `queued`, `uploading` (percent), `scanning`, `ready`, `rejected-type`, `rejected-size`, `failed` (network, with Retry), `infected` (blocked, not retryable, with guidance), `removed`. Each state has text and an icon; colours follow status tones. The component state: `idle`, `dragover` (outline), `busy`, `complete`, `has-errors`.

Announcements (polite, throttled to one every 2 seconds): "3 files added", "Exhibit-C.pdf uploaded, scanning", "Exhibit-C.pdf ready", "Exhibit-D.pdf failed to upload. Retry available". Errors that block submission are announced assertively once.

<!-- section:api -->
## Props API

```ts
type UploadItem = { clientId: string; name: string; size: number; type: string; status: UploadStatus; progress?: number; documentId?: string; error?: string };
export type FileDropzoneProps = FieldCommon & {
  accept: string[];                  // MIME types, e.g. ['application/pdf', 'image/png']
  maxFileSize: number;               // bytes; from tenant settings
  maxFiles?: number;
  mode?: 'single' | 'multiple' | 'ordered';
  requestUpload: (f: File) => Promise<{ uploadUrl: string; fields?: Record<string, string>; documentId: string }>; // tRPC call that returns a signed URL
  subscribeScanStatus: (documentId: string, cb: (s: 'scanning' | 'ready' | 'infected') => void) => () => void;
  items: UploadItem[]; onItemsChange: (items: UploadItem[]) => void;   // controlled
};
```

<!-- section:behaviour -->
## Behaviour

Files are checked client-side for type and size before upload (repeated server-side). Upload uses the signed URL (multipart for files over 100 MB, up to the tenant limit), runs at most 3 in parallel, and resumes or retries failed parts. Scan status arrives through the caller's subscription (server-sent events or polling from a tRPC procedure). The parent form may not submit while any file is `uploading` or `scanning`; the submit button explains why. Leaving the page with active uploads triggers a browser confirmation.

<!-- section:keyboard -->
## Keyboard, focus and assistive technology

"Choose files" is a normal button (Enter / Space). Each file row's Retry, Remove, Move up and Move down are buttons with names that include the file name ("Remove Exhibit-C.pdf"). After removal, focus moves to the next row's Remove button, or to "Choose files" if the list is empty. WCAG: 2.1.1, 2.5.7, 3.3.1, 4.1.3 [R2].

<!-- section:content -->
## Content guidelines

Hint: "PDF, DOCX or JPG, up to 200 MB each". Errors: "Exhibit-D.exe is not an accepted file type. Upload PDF, DOCX or JPG." / "This file may contain malware and was blocked. Check the file and upload a clean copy." Never show scanner internals.

<!-- section:tokens -->
## Tokens used

`dropzone.border.{default,dragover}` (dashed `border.control`), `dropzone.bg.dragover`, progress tokens (`progress.track`, `progress.fill` = action.primary.bg), status tones, `space.stack.sm`.

<!-- section:responsive -->
## Responsive behaviour and direction

On touch devices the drop area text is hidden and only "Choose files" shows. Long file names wrap and are never truncated without a full-name tooltip and accessible name.

<!-- section:examples -->
## Usage examples

```tsx
<FileDropzone label={t('filing.exhibits')} hint={t('filing.exhibitsHint')} accept={['application/pdf']} maxFileSize={tenant.limits.maxUpload}
  requestUpload={(f) => trpc.documents.createUpload.mutate({ caseId, name: f.name, size: f.size, type: f.type })}
  subscribeScanStatus={subscribe} items={items} onItemsChange={setItems} mode="ordered" />
```

<!-- section:testing -->
## Testing

Common to all components (see [[PKG-design-system-component]]): Storybook stories per variant × state, play-function interaction tests including the keyboard-only path, axe-core on every story (serious and critical fail the build), Playwright visual snapshots in a pinned Docker image across 5 fixture themes × light / dark / high contrast, plus RTL where layout is direction-dependent, and a forced-colours snapshot (Chromium `forcedColors: 'active'` emulation). Manual screen reader pass each release per the AT matrix in [[APP-accessibility-wcag-2-1-aa]] (NVDA + Chrome / Firefox, JAWS + Chrome on managed Windows, VoiceOver + Safari on macOS and iOS, TalkBack + Chrome on Android).

Specific: tests with a mocked upload server for slow network, failure and retry, infected result, 50-file list, and keyboard-only ordering.

<!-- section:questions -->
## Open questions

- [ ] Maximum per-file size per tenant plan (proposed default 200 MB; audio for transcription larger) (owner: product, with [[BIL-plans-entitlements-and-usage]]).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Assistive technology conformance

Native picker button always available, so drag and drop is optional; ordering by buttons; progress uses `<progress>` with labels; throttled polite announcements; row actions named with the file name; focus managed after removal.

<!-- check:api-design -->
### API design and misuse resistance

Controlled `items` list with injected `requestUpload` and `subscribeScanStatus`, so storage and scanning stay in server packages.

<!-- check:security -->
### Data safety in the component

Signed upload URLs are issued by the server per file under tenant and case permission; client type and size checks are repeated server-side; files are not viewable until the malware scan returns `ready`; file names are rendered as text only.

<!-- check:resilience -->
### Async, errors and edge cases

Parallel limit of 3, multipart retry, per-file Retry, form submission blocked during upload or scan, navigation warning with active uploads.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "excerpt": "Functionality that uses dragging can be achieved by a single pointer without dragging.",
    "id": "R1",
    "ident": "WCAG 2.2 SC 2.5.7",
    "kind": "standard",
    "title": "Understanding SC 2.5.7 Dragging Movements",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/dragging-movements"
  },
  {
    "body": "W3C",
    "excerpt": "Status messages can be programmatically determined so that assistive technologies can present them without receiving focus.",
    "id": "R2",
    "ident": "WCAG 2.2 SC 4.1.3",
    "kind": "standard",
    "title": "Understanding SC 4.1.3 Status Messages",
    "url": "https://www.w3.org/WAI/WCAG22/Understanding/status-messages"
  }
]
```

<!-- end -->
