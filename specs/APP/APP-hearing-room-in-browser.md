---
id: "APP-hearing-room-in-browser"
title: "Hearing room (in-browser)"
parent: "APP-party-and-counsel-portal"
order: 1
type: "requirement"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Frontend sub-architecture for live hearings: video SDK loading, permissions policy, reconnection, low-bandwidth mode"
links: []
rev: 3
syncHash: "09eeb12fd84c73d5"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.1.2.1.1 Hearing room (in-browser)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Frontend sub-architecture for live hearings: video SDK loading, permissions policy, reconnection, low-bandwidth mode

<!-- section:scope -->
## Scope, audiences and surfaces

Frontend sub-architecture for joining and taking part in a live virtual hearing in the browser. The same room component (`@nomology/hearing-room`) is mounted under three route groups so each persona keeps its own shell and permissions:

| Route | Personas |
|---|---|
| `/portal/cases/[caseRef]/hearings/[hearingId]/room` | parties, counsel, witnesses invited through a party |
| `/tribunal/cases/[caseRef]/hearings/[hearingId]/room` | neutrals (host controls) |
| `/secretariat/cases/[caseRef]/hearings/[hearingId]/room` | tribunal secretary, case manager (host and moderator controls) |

Covers: pre-join device and network check, lobby, loading the video provider SDK, permissions policy, in-room layout (participants, active speaker, pinned interpreter, captions, chat, shared exhibit), reconnection and low-bandwidth mode, leaving and post-hearing state.

Out of scope: the provider integration, room creation and recordings ([[INT-video-conferencing-for-hearings]]); hearing scheduling and attendance records ([[DOM-hearings]]); accessibility requirements for captions, CART and interpretation ([[DOM-hearing-room-accessibility]]), which this node implements.

<!-- section:routing -->
## Routes, layouts and boundaries

```text
.../hearings/[hearingId]/
  room/
    page.tsx        # server: authorise participant + hearing state; renders <HearingRoom> client island
    loading.tsx     # "Preparing the hearing room"
    error.tsx       # room-level boundary: offers phone dial-in and support reference
  room/check/page.tsx  # pre-join device, network and caption test (no SDK join)
```
The server page checks that the user is on the hearing's attendee list (or is a host persona) and that the hearing is within its join window (proposed: 30 minutes before start until it ends). It then mints a short-lived provider join token through `hearings.issueJoinToken` (server-side, never exposed beyond the client island's props) with the participant's display role (Arbitrator, Counsel for Claimant, Interpreter). Outside the join window the page shows the scheduled time with time zones.

<!-- section:rendering -->
## Rendering and caching strategy

Dynamic, `private, no-store`. The page HTML is a light server-rendered frame (hearing title, time, participant role, check list); the room is a client component loaded with `next/dynamic` (`ssr: false`) and the provider SDK is loaded only after the user selects "Join". No room state is cached on the server.

<!-- section:data -->
## Data fetching and mutations

| Operation | Kind | Notes |
|---|---|---|
| `hearings.getRoomContext` | server read | hearing, participant role, interpreter and CART assignments, caption languages |
| `hearings.issueJoinToken` | tRPC mutation | token valid 5 minutes for one join; re-issued on reconnect; rate limited to 10 per user per hearing per hour |
| `hearings.roomState` | tRPC query, polled every 10 s (or provider data channel) | session started, recording on, current exhibit, hearing paused |
| `hearings.shareExhibit` | tRPC mutation (host and presenting counsel) | shares a document page reference; others open it in the sandboxed viewer, not as screen share |
| `hearings.raiseObjection` / `requestToSpeak` | provider data message + audit via tRPC | |
| Attendance | provider webhooks to [[DOM-hearings]] | the browser does not report attendance itself |

<!-- section:state -->
## Client state and URL state

Local component state only: device selection, layout choice, low-bandwidth toggle, caption language, pinned tiles. Device and caption preferences are remembered per user in `localStorage` under `{userId}:hearing-prefs` (no case data). Nothing persists after leaving except those preferences.

<!-- section:errors -->
## Error, loading and empty handling

| Situation | Handling |
|---|---|
| Camera or microphone permission denied | Explain how to allow it for this site, with per-browser steps; offer "Join with audio only" and phone dial-in number |
| SDK fails to load (blocked network, old browser) | Room `error.tsx`: dial-in details, supported browsers list, support reference |
| Network drop | Provider reconnect with backoff (1, 2, 4, 8, 15 s, then every 15 s up to 2 minutes); banner "Reconnecting…" announced politely; tiles freeze, captions keep last line |
| Reconnect fails after 2 minutes | Prompt to rejoin (new token) or dial in; host sees the participant as "Disconnected" |
| Bandwidth below 300 kbps for 10 s | Offer low-bandwidth mode; switch automatically if below 150 kbps |
| Hearing ended by host | Show "The hearing has ended" with next steps; do not auto-close for screen-reader users |

<!-- section:performance -->
## Performance budgets

- Room page shell (before SDK): ≤ 120 KB gzip JS, LCP ≤ 2.5 s on mid-range Android over slow 4G.
- SDK chunk is excluded from route budgets but measured: join-to-first-audio p75 ≤ 5 s on broadband, ≤ 10 s on 4G (proposed).
- **Low-bandwidth mode**: receive only active speaker plus pinned interpreter at 360p (or audio only), disable own video, pause shared-screen video in favour of the exhibit viewer; target ≤ 300 kbps down.
- CPU: virtual backgrounds and blur are off by default on mobile.

<!-- section:security -->
## Security headers and browser session

- Permissions-Policy on room routes only: `camera=(self), microphone=(self), display-capture=(self)` if the provider SDK runs in our page; if the provider uses an iframe embed, `camera=(self "https://<provider-host>")` and the iframe carries `allow="camera; microphone; display-capture"`. Every other route keeps `camera=(), microphone=()`.
- CSP on room routes adds the provider's script, `connect-src` (HTTPS and WSS) and `media-src` hosts for the tenant's region only.
- Join tokens are single-use, 5-minute, bound to participant and hearing; the room never receives provider API keys.
- Screen sharing by parties is off by default and allowed per hearing by the host; exhibits are shared as page references so the record shows what was shown.
- Private breakout rooms for a party and its counsel are provider rooms with their own tokens; the tribunal cannot join them, and they are never recorded (to be confirmed against each tenant's rules).

<!-- section:i18n -->
## Localisation hookup

UI strings in `hearing` namespace. Caption language is selectable per participant from the languages assigned to the hearing; interpreter channels are labelled with language names in that language (for example "हिन्दी", "中文") with `lang` attributes.

<!-- section:observability -->
## Frontend observability

Client metrics (no content, no names): join time, reconnect count and duration, low-bandwidth mode activations, SDK errors by code, device-permission denials. Tagged with tenant, region, hearing ID hash, persona. Provider quality metrics are pulled server-side by [[INT-video-conferencing-for-hearings]].

<!-- section:testing -->
## Testing strategy

- Pre-join check and join flow in Playwright with fake media devices (Chromium `--use-fake-device-for-media-stream`) for each persona route.
- Network throttling tests: drop for 30 s and 3 minutes; bandwidth at 150 kbps.
- Manual AT testing of the room with NVDA, JAWS, VoiceOver (macOS and iOS) and TalkBack per [[DOM-hearing-room-accessibility]].
- Header test asserting Permissions-Policy differs between room and non-room routes.

<!-- section:questions -->
## Open questions

- [ ] Video provider per region, and whether it is an SDK in our page or an iframe embed; drives Permissions-Policy and CSP (owner: TERES product, [[INT-video-conferencing-for-hearings]])
- [ ] Join window (30 minutes before start) and whether witnesses join through the counsel portal or a separate guest link (owner: product with institution tenants)
- [ ] Are party breakout rooms required by any tenant's procedure, and must they be excluded from recording? (owner: legal)
- [ ] Phone dial-in availability per region (owner: TERES product)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

The room page authorises the participant against the hearing in the tenant transaction; join tokens are bound to tenant, hearing and participant. Provider rooms are created per hearing with tenant-scoped names (no case titles); a token for one tenant's hearing cannot join another's room.

<!-- check:browser-security -->
### Browser security posture

Camera, microphone and display capture are allowed only on room routes; elsewhere Permissions-Policy denies them. The provider SDK and its hosts are allowed in CSP only on room routes and only for the tenant's region. Exhibits shown in the hearing open in the sandboxed document origin.

<!-- check:resilience -->
### Failure, deploys and version skew

Reconnect with backoff for 2 minutes, then rejoin with a fresh token; low-bandwidth mode automatic below 150 kbps; phone dial-in offered whenever the SDK fails. A rolling deploy does not affect a joined room because the room is a client island that keeps its connection; only the next server request triggers a reload.

<!-- check:accessibility -->
### App-level accessibility mechanics

All room controls are reachable by keyboard; shortcuts use modifier keys or can be turned off (WCAG 2.1.4); captions panel is a live region the user can pause; interpreter tile can be pinned and enlarged; chat messages announce politely. Detailed criteria in [[DOM-hearing-room-accessibility]].

<!-- check:residency -->
### Region, residency and telemetry privacy

The provider must offer media routing and recording storage in the tenant's region; CSP limits the browser to that region's provider hosts. Where a provider cannot route media in region, the tenant must accept it in its contract (recorded in [[INT-third-party-component]]).

<!-- check:supply-chain -->
### Framework upgrades and supply chain

The provider SDK is a third-party runtime script with camera access, so it is pinned to a version, loaded from the provider's versioned URL (or self-hosted if licence allows), covered by a vendor assessment in [[SEC-vendor-sub-processor-management]], and upgraded through a preview environment with the room test suite.

<!-- end -->
