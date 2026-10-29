---
id: "INT-video-conferencing-for-hearings"
title: "Video conferencing for hearings"
parent: "INT-common-integrations"
order: 1
type: "feature"
template: "integration"
status: "draft"
owner: null
indicative: false
summary: "Provider integration for virtual hearing rooms, calendar invites, recordings and transcript hand-off, per region"
links: []
rev: 2
syncHash: "7c68e6768f5b22a5"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 9.2.1 Video conferencing for hearings

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Provider integration for virtual hearing rooms, calendar invites, recordings and transcript hand-off, per region

<!-- section:purpose -->
## Purpose and use cases

Virtual and hybrid hearings need audio / video rooms that participants join from the platform, with recordings that become part of the case record and feed transcription. Use cases:
1. Create a room when a hearing is scheduled ([[DOM-hearings]]), with lobby / waiting room controlled by the tribunal secretary.
2. Participants join from the in-browser hearing room ([[APP-hearing-room-in-browser]]) with a short-lived token bound to their identity and role (neutral, party, counsel, witness, interpreter, transcriber, observer).
3. Breakout rooms for private consultation (party with counsel); the tribunal can not see inside them and they are never recorded.
4. Record the main room when the tribunal starts recording; receive the recording, store it in our regional bucket and hand it to transcription ([[WF-long-running-pipelines]], [[DOM-transcribers]]).
5. Capture attendance (join / leave times) as hearing evidence ([[DOM-hearings-schema]]).
6. Live captions and interpreter pinning where the provider supports them ([[DOM-hearing-room-accessibility]]).

<!-- section:party -->
## External party and ownership

Provider **not chosen**. Two options to evaluate:
- **A. Managed video SDK provider** with media servers and recording storage selectable per region (India, Singapore, US). Needs confirmed in-region media routing and recording storage for each region.
- **B. Self-hosted open-source media servers** (SFU) per region on our ECS / Azure clusters, with recordings written straight to our bucket. More control of residency, more operations work.

Embedding external meeting apps (joining via a third-party meeting link) is allowed only as a tenant-chosen fallback, because recordings and attendance then sit outside our control.

Contract owner: TERES product lead; technical owner: hearings team. Environments: sandbox project per region for dev / staging / UAT; production project per region.

<!-- section:flows -->
## Data flows

```
Secretariat schedules hearing
  └─▶ Temporal hearings workflow `{tenantId}-hearing-{hearingId}`
        ├─ activity video.createRoom(hearingId, region, settings) ─▶ provider (idempotency `room:{hearingId}`)
        ├─ timer until T-15 min: open lobby
        ├─ (participant clicks Join) Route Handler POST /api/hearings/{id}/join-token
        │     └─ policy check (participant of hearing, not removed) ─▶ provider token (TTL 10 min, role, display name)
        ├─ signal recordingStarted / recordingStopped (from provider webhook via inbox)
        ├─ signal recordingReady {providerRecordingId}
        │     └─ activity video.fetchRecording ─▶ stream to s3://{region}-hearings/{tenantId}/{hearingId}/{recordingId}.mp4
        │          └─ malware scan, SHA-256, create document version, emit hearing.recording_available
        │          └─ start child workflow transcription `{tenantId}-transcribe-{recordingId}`
        │          └─ activity video.deleteProviderRecording (after hash verified)
        └─ hearing ended: activity video.closeRoom; attendance pulled and stored
```
Join is synchronous (user waits, target p95 < 800 ms); everything else is asynchronous.

<!-- section:mapping -->
## Data mapping

| Our field | Provider field | Direction | Personal data | Notes |
|---|---|---|---|---|
| `hearing.id` | room name / external ID `{tenantId}:{hearingId}` | out | no | Opaque; no case title |
| hearing start, end, time zone | room schedule (UTC) | out | no | |
| participant display name | token `name` | out | yes | Role label added: "Counsel for Claimant" (tenant setting) |
| participant role | token grants (publish, subscribe, record, admit) | out | no | From hearing role |
| user ID | token `identity` = `{participantId}` | out | pseudonymous | Never email |
| — | participant IP, device, media | provider-held | yes | Provider data; covered by DPA |
| recording file | provider recording | in | yes (voice, image) | Copied to our bucket, then deleted at provider |
| attendance join / leave | provider participant events | in | yes | Stored as `hearing_attendance` rows |
| captions (if any) | provider live transcript | in | yes | Not the official transcript; marked machine-generated |

<!-- section:auth -->
## Authentication and secrets

Outbound: provider API key / secret or signing key per region in the regional secrets manager (`/{env}/{region}/integrations/video/platform`); room join tokens are JWTs signed by our server with the provider's signing key, 10-minute TTL, single room, role-limited grants. Inbound: provider webhooks verified by signature (provider scheme) and replay-protected via the inbox. Rotation every 90 days with dual-key overlap.

<!-- section:errors -->
## Errors, retries and idempotency

| Situation | Handling |
|---|---|
| Room creation fails (5xx / timeout) | Temporal retries with backoff up to 2 h; at T-24 h without a room, human task to secretariat |
| Token mint fails at join | Retry once inline; then show "We cannot connect you to the hearing room right now" with dial-in or support details; alert |
| Duplicate `recording.ready` | Inbox de-dupes on provider event ID; activity idempotent on `recording:{providerRecordingId}` |
| Recording download interrupted | Resumable ranged download with heartbeats; restart from last offset |
| Hash mismatch after copy | Retry download; never delete provider copy until hash matches |
| Provider outage during a hearing | Participants see reconnecting state ([[APP-hearing-room-in-browser]]); tribunal secretary may adjourn; attendance gap recorded |

<!-- section:limits -->
## Rate limits and SLAs

Expected (proposed, Year 1): 3,000 hearing hours per month, up to 60 concurrent rooms per region at peak, 25 participants per room typical (100 max for large hearings with observers). Recording storage about 0.5–1 GB per hour (720p composite; to confirm). Provider SLA needed: 99.9% monthly, with regional failover inside the same jurisdiction only.

<!-- section:residency -->
## Data transfer and compliance

Media for a tenant's hearings must be routed and recorded in the tenant's region; recordings are stored long-term only in our regional bucket. If option A cannot guarantee in-region media for a region, option B is used there. Participants abroad (for example foreign counsel) connect to the regional media servers; their connection does not move the data. Provider breach notice must be fast enough for CERT-In's 6-hour reporting window for Indian incidents [R1].

<!-- section:testing -->
## Sandbox and testing

Sandbox room per environment; synthetic hearing (two bot participants, 2-minute recording) daily in staging per region, checking recording copy, hash and transcription start. Load test at 60 concurrent rooms. Low-bandwidth and reconnection tests in the hearing room frontend.

<!-- section:questions -->
## Open questions

- [ ] Option A (managed provider) or B (self-hosted) per region; record as an ADR after a residency and cost comparison.
- [ ] Are breakout rooms ever recorded? Proposed: never, and the UI states this.
- [ ] Recording format: composite only, or separate audio tracks per speaker to improve transcription?
- [ ] Is a phone dial-in fallback required by any institution's rules?
- [ ] Retention of provider-side copies: delete immediately after verified copy (proposed).

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant separation at the provider

One platform project per region at the provider; rooms are named with opaque `{tenantId}:{hearingId}` and every webhook is mapped by connection and room name to one tenant, then the hearing is loaded under RLS before any write. Join tokens are minted only after the policy check that the user is a participant of that hearing.

<!-- check:residency -->
### Data transfer and residency

In-region media and recording are a selection criterion; long-term recordings live only in our regional bucket, provider copies are deleted after a verified copy. Personal data at the provider: display name, pseudonymous participant ID, IP and media.

<!-- check:resilience -->
### Failure handling and degradation

Room creation runs days ahead with retries and a human task at T-24 h; join has an inline single retry with a clear fallback message; recording copy is resumable and hash-verified before provider deletion.

<!-- check:consistency -->
### Consistency and reconciliation

Hearing status is owned by the platform; the provider is authoritative only for media events (recording ready, participant joined / left). A nightly job lists provider recordings older than 24 hours that have no copied version and alerts.

<!-- check:audit -->
### Audit and evidence

Room created, recording started / stopped, recording copied (with SHA-256), attendance, and token mints (participant, time, role) are audited per hearing. The recording is an immutable document version in the case record.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Reportable cyber incidents must be reported to CERT-In within 6 hours of being noticed.",
    "id": "R1",
    "issuer": "CERT-In, Ministry of Electronics and Information Technology",
    "jurisdiction": "India",
    "kind": "regulation",
    "title": "Directions under section 70B(6) of the IT Act, 28 April 2022",
    "url": "https://www.cert-in.org.in/Directions70B.jsp"
  }
]
```

<!-- end -->
