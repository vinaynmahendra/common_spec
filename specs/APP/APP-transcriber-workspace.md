---
id: "APP-transcriber-workspace"
title: "Transcriber workspace"
parent: "APP-route-groups-per-persona"
order: 4
type: "requirement"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Frontend architecture for the (transcriber) route group: audio/video player, transcript editor, turnaround tracking"
links: []
rev: 2
syncHash: "33e02051984a7179"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.1.2.4 Transcriber workspace

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Frontend architecture for the (transcriber) route group: audio/video player, transcript editor, turnaround tracking

<!-- section:scope -->
## Scope, audiences and surfaces

Frontend architecture of the `(transcriber)` route group, prefix `/transcription`. Personas: transcribers and transcript reviewers, who may be tenant staff or external vendors working for TERES ([[DOM-transcribers]]). They see only what an assignment needs: the recording segment, the case reference, the hearing date and speaker labels.

Covers: assignment queue with turnaround timers, media player, transcript editor with timestamps and speaker turns, machine draft import, review and certification, and delivery.

Out of scope: speech-to-text pipeline ([[WF-long-running-pipelines]]), vendor billing ([[DOM-invoices-and-vendor-bills]]), recordings storage ([[INT-video-conferencing-for-hearings]]).

<!-- section:routing -->
## Routes, layouts and boundaries

```text
app/(transcriber)/transcription/
  layout.tsx                               # shell; requirePersona('transcriber' | 'transcript-reviewer')
  page.tsx                                 # my assignments with due times
  assignments/[assignmentId]/
    page.tsx                               # player + editor (client island)
    error.tsx  not-found.tsx
    review/page.tsx                        # reviewer view with diff against previous version
    certify/page.tsx                       # certification statement + step-up
  history/page.tsx                         # completed assignments (no media access)
```
Access is by assignment, not by case: `getAssignmentForTranscriber` checks that the assignment belongs to the user and is open. A closed assignment returns not-found for media and editor routes.

<!-- section:rendering -->
## Rendering and caching strategy

Dynamic, `private, no-store`. The editor and player are a client island; the server renders assignment metadata and the due time. Media is streamed from regional object storage with short-lived signed URLs (HTTP range requests), never through the Next.js server.

<!-- section:data -->
## Data fetching and mutations

| Operation | Kind | Notes |
|---|---|---|
| `transcription.assignments.list` | tRPC query | due time, turnaround target, status |
| `transcription.media.getUrl` | tRPC mutation | signed URL valid 15 minutes, renewed by the player before expiry; bound to assignment |
| `transcription.segments.save` | tRPC mutation | autosave per segment edit (debounced 2 s); `segmentVersion` concurrency |
| `transcription.submitForReview` | tRPC mutation | |
| `certifyTranscript` | Server Action | certification statement version recorded; step-up; generates PDF/UA and timed text (WebVTT) |

<!-- section:state -->
## Client state and URL state

Segment edits are held in memory and an IndexedDB shadow until acknowledged. Player position, playback speed and shortcut preferences are kept per user in `localStorage` (no case data).

<!-- section:forms -->
## Forms, validation and uploads

Certification uses a declaration from [[I18N-legal-declaration-and-consent]] with version ID stored. The editor validates timestamps are monotonic and speakers are from the hearing's speaker list.

<!-- section:errors -->
## Error, loading and empty handling

| Situation | Handling |
|---|---|
| Assignment closed or reassigned | Not-found page; local shadow is discarded after telling the user |
| Signed URL expired | Player renews silently; after 3 failures shows "Media could not be loaded" with retry |
| Segment save conflict | Reviewer edits win only through review flow; conflict dialog shows both versions |
| Turnaround breached | Banner on the assignment and notice to the coordinator; editor still works |

<!-- section:performance -->
## Performance budgets

≤ 300 KB gzip first-load JS including editor; keystroke to render INP ≤ 100 ms for transcripts up to 8 hours of audio (about 60,000 words), using a virtualised segment list. Waveform rendered from precomputed peaks (JSON) rather than decoding audio in the browser.

<!-- section:security -->
## Security headers and browser session

- Media downloads are not offered; the player uses blob-less streaming with signed URLs bound to the assignment (copying is still possible, so vendor contracts carry confidentiality terms).
- A visible, per-user watermark (name and assignment reference) is overlaid on video (proposed).
- External transcribers see speaker labels and the case reference only; party contact details and documents are never in their view objects.
- Certification requires step-up.

<!-- section:i18n -->
## Localisation hookup

Namespace `transcription`. Transcript language follows the hearing language; mixed-language segments can be marked with a language so `lang` is set in the output.

<!-- section:observability -->
## Frontend observability

Metrics: time from assignment to first edit, words per hour (aggregate, not per person in dashboards visible to vendors), save failures, turnaround breaches. Quality review scores belong to [[DOM-transcribers]].

<!-- section:testing -->
## Testing strategy

Playwright: edit, autosave, conflict, certify with step-up. Keyboard-only editing with play/pause and seek shortcuts. Access tests: expired assignment cannot fetch media URL.

<!-- section:questions -->
## Open questions

- [ ] Play and seek shortcuts that do not clash with screen-reader keys (proposed: Ctrl+Space play/pause, Ctrl+, and Ctrl+. seek 5 s), and whether users can remap them (owner: UX)
- [ ] Is a visible watermark required by tenants, and is it acceptable for transcribers with low vision? (owner: product, security)
- [ ] Do external vendor transcribers sign in through the tenant host, or through a vendor host spanning tenants? (owner: TERES product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

Access is granted per assignment inside the tenant transaction; media signed URLs are bound to tenant, assignment and expiry. A transcriber working for two tenants uses two hosts and two query caches.

<!-- check:data-exposure -->
### Server boundary and data exposure

View objects for transcribers contain only what the assignment needs (media, speaker labels, case reference, due time); no party contacts, no documents, no other assignments of the same case.

<!-- check:session -->
### Sessions in the browser

60 min idle and 12 h absolute; segment autosave means expiry loses at most 2 seconds of typing; certification requires step-up; on shared vendor machines the 'shared device' option applies.

<!-- check:resilience -->
### Failure, deploys and version skew

Per-segment autosave every 2 seconds with a local shadow; signed URL renewal before expiry; a forced reload during deploy restores the editor at the same segment and playback position.

<!-- check:accessibility -->
### App-level accessibility mechanics

Shortcuts use modifiers and can be turned off; segment list is a list with timestamps announced; the player exposes accessible controls with labels and current time. Screen-reader users can edit while audio plays through a 'pause when typing' option.

<!-- check:residency -->
### Region, residency and telemetry privacy

Media streams directly from the tenant's regional bucket via signed URLs; the waveform peaks file and editor assets come from the same region; telemetry carries route templates and hashed assignment IDs only. External vendor transcribers working from other countries see data in the tenant's region through the browser, which is a cross-border access question for the vendor contract (see questions).

<!-- end -->
