---
id: "PKG-document-viewer-controls"
title: "Document viewer controls"
parent: "PKG-ui-design-system"
order: 14
type: "feature"
template: "component"
status: "draft"
owner: null
indicative: false
summary: "Viewer UI component: toolbar, page navigation, zoom, search, bundle page references; rendering and sandbox origin belong to the frontend node 'Document viewer and sandbox origin'"
links: []
rev: 2
syncHash: "f6c80a3b8315d73e"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.14.14 Document viewer controls

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Viewer UI component: toolbar, page navigation, zoom, search, bundle page references; rendering and sandbox origin belong to the frontend node 'Document viewer and sandbox origin'

<!-- section:purpose -->
## Purpose and when to use

`DocumentViewerToolbar` and related controls are the user interface around the document viewer: page navigation, zoom, fit modes, search within the document, rotate, download and print (if permitted), bundle page references ("Bundle B, Tab 3, page 47"), and the outline / bookmarks panel. Rendering, the sandboxed origin and annotation storage belong to [[APP-document-viewer-and-sandbox]]; this component talks to the viewer frame through a typed message channel.

<!-- section:anatomy -->
## Anatomy

| Part | Required | Element |
|---|---|---|
| Toolbar | Yes | `role="toolbar" aria-label="Document controls"` with roving tabindex |
| Page navigation | Yes | Previous / Next `IconButton`s, page number `TextField` ("Page 12 of 340"), bundle reference display |
| Zoom | Yes | Zoom out / in buttons, zoom select (50–400 percent, fit width, fit page) |
| Search | Yes | Search field, result count ("3 of 17"), previous / next result |
| Outline toggle | When document has bookmarks | Button controlling a side panel (`<nav aria-label="Bookmarks">` tree) |
| Go to bundle reference | eBundles | Input accepting "B/3/47" |
| Download / print | Permission-dependent | Buttons, hidden when the user lacks permission |
| Status line | Yes | Polite live region for page changes from search and "Go to" |

<!-- section:variants -->
## Variants and sizes

`document` (single file) and `bundle` (eBundle with tabs and bundle pagination from [[DOM-ebundling]]); `compact` toolbar in the neutral workspace split view.

<!-- section:states -->
## States

Loading document, ready, page rendering, search running, no matches, text layer unavailable (scanned document without OCR: search disabled with reason "This document has no searchable text. Request an accessible copy", linked to [[DOM-accessible-documents-and]]), error, permission-restricted (download hidden; watermark notice).

<!-- section:api -->
## Props API

```ts
export type ViewerChannel = {
  goToPage(n: number): void; setZoom(z: number | 'fit-width' | 'fit-page'): void; rotate(deg: 90 | -90): void;
  search(q: string): Promise<{ total: number }>; nextResult(): void; prevResult(): void;
  on(event: 'page-change' | 'search-result' | 'loaded' | 'error', cb: (p: unknown) => void): () => void;
};
export type DocumentViewerToolbarProps = {
  channel: ViewerChannel; pageCount: number; currentPage: number;
  bundle?: { resolveRef: (ref: string) => number | null; refForPage: (p: number) => string };
  permissions: { download: boolean; print: boolean };
  onDownload?: () => void; onPrint?: () => void;
};
```
The channel is a `postMessage` wrapper to the sandboxed origin with origin checks on both sides and a schema-validated message set.

<!-- section:behaviour -->
## Behaviour

Page changes from scrolling update the page field without announcement; changes from Go to, search or bookmarks announce "Page 47, Bundle B Tab 3". Keyboard shortcuts are active only when focus is in the viewer area. Download and print call server endpoints that check permission, issue a short-lived signed URL and write an audit event ([[PKG-audit-trail]]); the toolbar only hides buttons as a convenience. Client component, lazy-loaded with the viewer.

<!-- section:keyboard -->
## Keyboard, focus and assistive technology

| Key | Action |
|---|---|
| Tab | Enters the toolbar (one stop), then the document area |
| Left / Right in toolbar | Move between controls (roving tabindex) |
| Ctrl/Cmd+F in viewer | Focus search field |
| Enter / Shift+Enter in search | Next / previous result |
| Page Down / Page Up in document | Next / previous page |
| Ctrl/Cmd + / − / 0 in viewer | Zoom in, out, reset |
| G then page number (proposed) | Go to page |

Single-character shortcuts are not used without a modifier (WCAG 2.1.4). After "Go to", focus moves to the target page container. WCAG: 1.4.4 and 1.4.10 apply to the toolbar; the document content follows [[DOM-accessible-documents-and]]; 2.1.1, 2.1.4, 2.4.3, 4.1.2, 4.1.3.

<!-- section:content -->
## Content guidelines

Page field label "Page"; bundle reference format follows the tenant's practice ("B/3/47" or "Bundle B, Tab 3, p. 47"), configured per tenant.

<!-- section:tokens -->
## Tokens used

`toolbar.bg` (surface.subtle), `toolbar.border`, button tertiary tokens, `viewer.canvas.bg` (neutral.100 light / neutral.900 dark; the page itself is always rendered white), `elevation.1`.

<!-- section:responsive -->
## Responsive behaviour and direction

Below `md` the toolbar shows page navigation and an overflow menu for zoom, search and outline; pinch zoom works on touch. RTL mirrors toolbar order but page navigation arrows follow document reading direction.

<!-- section:examples -->
## Usage examples

```tsx
<DocumentViewerToolbar channel={viewer} pageCount={meta.pages} currentPage={page}
  bundle={meta.bundle && { resolveRef: meta.bundle.resolve, refForPage: meta.bundle.refFor }}
  permissions={perms} onDownload={() => download(docVersionId)} />
```

<!-- section:testing -->
## Testing

Common to all components (see [[PKG-design-system-component]]): Storybook stories per variant × state, play-function interaction tests including the keyboard-only path, axe-core on every story (serious and critical fail the build), Playwright visual snapshots in a pinned Docker image across 5 fixture themes × light / dark / high contrast, plus RTL where layout is direction-dependent, and a forced-colours snapshot (Chromium `forcedColors: 'active'` emulation). Manual screen reader pass each release per the AT matrix in [[APP-accessibility-wcag-2-1-aa]] (NVDA + Chrome / Firefox, JAWS + Chrome on managed Windows, VoiceOver + Safari on macOS and iOS, TalkBack + Chrome on Android).

Specific: channel contract tests against the sandbox viewer; 2,000-page bundle story; permission fixtures; scanned-document fallback state.

<!-- section:questions -->
## Open questions

- [ ] Bundle reference format per institution (owner: TERES product lead).
- [ ] Should print be allowed for parties by default (owner: product, legal).

<!-- checks -->
## Template checks

<!-- check:accessibility -->
### Assistive technology conformance

Toolbar with roving tabindex and one Tab stop, named controls, shortcuts with modifiers only, announcements for explicit navigation, clear fallback when a document has no text layer with a route to request an accessible copy.

<!-- check:security -->
### Data safety in the component

Messages to the sandboxed viewer origin are schema-validated with origin checks; download and print go through server endpoints that check permission, issue short-lived signed URLs and audit; hiding buttons is not relied on for access control.

<!-- check:resilience -->
### Async, errors and edge cases

Search over large bundles runs in the viewer worker with a progress status; failures show inline Retry; a document with no text layer disables search with a stated reason and a route to request an accessible copy.

<!-- check:performance -->
### Performance and bundle cost

The toolbar is lazy-loaded with the viewer; page rendering and large-bundle performance are owned by [[APP-document-viewer-and-sandbox]].

<!-- check:testing -->
### Test and documentation coverage

Contract tests for the postMessage channel against the sandbox viewer; stories for document and bundle variants, no-text-layer state, permission-restricted state and 2,000-page bundle; keyboard tests for roving tabindex and shortcuts.

<!-- end -->
