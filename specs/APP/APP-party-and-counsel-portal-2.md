---
id: "APP-party-and-counsel-portal-2"
title: "Party and counsel portal accessibility conformance"
parent: "APP-accessibility-wcag-2-1-aa"
order: 3
type: "requirement"
template: "accessibility"
status: "draft"
owner: null
indicative: false
summary: "WCAG 2.2 AA mapping, AT matrix and exceptions for the party / counsel route group"
links: []
rev: 2
syncHash: "967780d4d7c90fe7"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.4.1.3 Party and counsel portal accessibility conformance

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> WCAG 2.2 AA mapping, AT matrix and exceptions for the party / counsel route group

<!-- section:scope -->
## Scope and surfaces

Accessibility conformance for the `(counsel)` route group ([[APP-party-and-counsel-portal]]) and the `(public)` sign-in and filing-entry surfaces that lead into it ([[APP-public-and-sign-in-surfaces]]), including the counsel side of the hearing room ([[APP-hearing-room-in-browser]]) and the document viewer as used by parties ([[APP-document-viewer-and-sandbox]]). Users: unrepresented parties (often on Android phones, sometimes with low literacy or in Indian languages), counsel on laptops, and people assisting them. Out of scope: secretariat and neutral surfaces ([[APP-secretariat-console-and-neutral]]).

<!-- section:obligations -->
## Standards and legal obligations by jurisdiction

As in [[APP-accessibility-legal-obligations]]; this surface is the one most exposed to RPwD s.46 and the SEBI circular, because investors and MSME claimants use it directly.

<!-- section:target -->
## Conformance target and baseline

WCAG 2.2 AA; EN 301 549 clause 6 for the hearing room; PDF/UA for receipts and notices this surface generates. Baseline: to be measured at the Phase 3 audit.

<!-- section:criteria -->
## Success criteria mapping

Scope: `(counsel)` and `(public)` surfaces. "DS" = design-system component with its accessibility contract ([[PKG-design-system-component]]). Tests: A = axe automated, K = keyboard Playwright, M = manual expert review, AT = AT matrix run.

| SC | Level | Where met | How | Test |
|---|---|---|---|---|
| 1.1.1 Non-text Content | A | DS icons, logos, status icons, file-type icons | icon buttons have accessible names; decorative icons `aria-hidden`; tenant logo alt = tenant name | A, M |
| 1.2.1 Audio/Video-only | A | recordings page | transcript offered with every recording | M |
| 1.2.2 Captions (Prerecorded) | A | recordings | captions from certified transcript (WebVTT) | M |
| 1.2.3 Audio Description or Media Alt | A | recordings | transcript as media alternative; hearings rarely carry essential visual-only content (assumption) | M |
| 1.2.4 Captions (Live) | AA | hearing room | live captions / CART ([[DOM-hearing-room-accessibility]]) | M, AT |
| 1.2.5 Audio Description (Prerecorded) | AA | recordings | exhibits shown in hearings are referenced by bundle page in the transcript | M |
| 1.3.1 Info and Relationships | A | all pages | headings, lists, tables with headers, fieldsets for radio groups, `aria-describedby` for hints and errors (DS form fields) | A, M |
| 1.3.2 Meaningful Sequence | A | all | DOM order matches visual order; no CSS reordering of content | M |
| 1.3.3 Sensory Characteristics | A | copy | instructions never rely on shape or position ([[APP-voice-tone-and-content-style]]) | M |
| 1.3.4 Orientation | AA | all | no orientation lock (RESP-7) | A |
| 1.3.5 Identify Input Purpose | AA | profile, sign-in, filing party details | `autocomplete` tokens on personal fields | A, M |
| 1.4.1 Use of Color | A | stage and deadline badges | text and icon besides colour ([[PKG-status-and-deadline-badges]]) | M |
| 1.4.2 Audio Control | A | hearing room, recordings | no autoplay audio outside an explicit join | M |
| 1.4.3 Contrast (Minimum) | AA | tokens, tenant themes | contrast-pair manifest; theme activation blocked on failure | A, CI |
| 1.4.4 Resize Text | AA | all | rem units, 200% text without loss | M |
| 1.4.5 Images of Text | AA | all | no images of text except logos | M |
| 1.4.10 Reflow | AA | all; viewer and tables scroll in region | RESP-3 | automated + M |
| 1.4.11 Non-text Contrast | AA | inputs, focus ring, icons | tokens 3:1 | CI, M |
| 1.4.12 Text Spacing | AA | all | no fixed heights; tested with spacing bookmarklet | M |
| 1.4.13 Content on Hover or Focus | AA | tooltips, popovers (DS) | dismissable with Esc, hoverable, persistent | M |
| 2.1.1 Keyboard | A | all, incl. dropzone keyboard alternative and viewer | DS keyboard models | K, M |
| 2.1.2 No Keyboard Trap | A | modals, viewer iframe, payment widget | focus returns; iframe exit documented | K, M |
| 2.1.4 Character Key Shortcuts | A | hearing room, viewer | shortcuts use modifiers or can be turned off | M |
| 2.2.1 Timing Adjustable | A | session warning; OTP 10 min; draft autosave | extend option; no loss on expiry | K, M |
| 2.2.2 Pause, Stop, Hide | A | carousels none; live caption scroll | captions can be paused | M |
| 2.3.1 Three Flashes | A | all | no flashing content | M |
| 2.4.1 Bypass Blocks | A | layouts | skip link, landmarks | A |
| 2.4.2 Page Titled | A | all | "{Page} – {Case ref} – {Tenant}" | automated |
| 2.4.3 Focus Order | A | stepper, modals, drawers | focus moved to step heading / dialog; returned on close | K |
| 2.4.4 Link Purpose (In Context) | A | lists of documents and filings | link text names the item | M |
| 2.4.5 Multiple Ways | AA | portal | navigation, case search, notifications links | M |
| 2.4.6 Headings and Labels | AA | all | descriptive headings and labels from content patterns | M |
| 2.4.7 Focus Visible | AA | tokens | non-overridable focus ring | M |
| 2.4.11 Focus Not Obscured (Minimum) | AA | sticky header, cookie / offline banners | `scroll-padding-top`; banners do not cover focus | K, M |
| 2.5.1 Pointer Gestures | A | viewer zoom, upload | buttons for zoom; no multipoint-only gestures | M |
| 2.5.2 Pointer Cancellation | A | buttons (DS) | activation on up-event | M |
| 2.5.3 Label in Name | A | icon+text buttons | visible text included in accessible name | A, M |
| 2.5.4 Motion Actuation | A | — | no motion-triggered functions | N/A with reason: no device-motion features |
| 2.5.7 Dragging Movements | AA | file dropzone, document reorder in filing | "Choose files" button; move up/down buttons | K, M |
| 2.5.8 Target Size (Minimum) | AA | all | 24 px minimum, 44 px primary on touch | A |
| 3.1.1 Language of Page | A | root layout | `lang` from locale | automated |
| 3.1.2 Language of Parts | AA | document titles, quoted text in other languages | `lang` from metadata | M |
| 3.2.1 On Focus | A | all | no context change on focus | M |
| 3.2.2 On Input | A | filters, language switcher | changes apply on explicit action or are announced | M |
| 3.2.3 Consistent Navigation | AA | persona shell | same nav order | M |
| 3.2.4 Consistent Identification | AA | DS + glossary | same labels for same functions ([[I18N-platform-glossary-and]]) | M |
| 3.2.6 Consistent Help | A | layouts | help and accessibility contact in the same place | M |
| 3.3.1 Error Identification | A | forms | error summary + inline errors in text | A, M |
| 3.3.2 Labels or Instructions | A | forms | visible labels, hints, required marked in text | A, M |
| 3.3.3 Error Suggestion | AA | forms | messages say how to fix ([[APP-error-message-catalogue]]) | M |
| 3.3.4 Error Prevention (Legal, Financial, Data) | AA | submit filing, pay, withdraw, accept terms | review step, consequential confirmation, and filings can be corrected through an amendment route; payments confirmed before charge ([[PKG-modal-dialog-and-consequential]]) | K, M |
| 3.3.7 Redundant Entry | A | filing stepper, profile | party details reused from profile and previous filings | M |
| 3.3.8 Accessible Authentication (Minimum) | AA | sign-in, step-up | paste, password managers, magic link, passkeys | M |
| 4.1.2 Name, Role, Value | A | DS components | APG patterns | A, AT |
| 4.1.3 Status Messages | AA | upload progress, save status, toasts | polite live regions ([[PKG-alerts-toasts-and-status]]) | AT |

4.1.1 Parsing is obsolete in WCAG 2.2 and not mapped.

<!-- section:components -->
## Component and pattern requirements

| Component | Contract essentials |
|---|---|
| [[PKG-stepper-and-multi-step-form]] | step heading focus on change; "Step n of m" announced; save status as status message |
| [[PKG-form-fields]] | label, hint and error tied with `aria-describedby`; error summary with links |
| [[PKG-file-upload-dropzone]] | button alternative to drag and drop; per-file status announced; scan result announced |
| [[PKG-modal-dialog-and-consequential]] | APG dialog; consequence stated in heading; focus return |
| [[PKG-case-timeline]] | list semantics with dates as text; filters labelled |
| [[PKG-status-and-deadline-badges]] | text plus icon; absolute date with time zone |
| [[PKG-document-viewer-controls]] | toolbar pattern; page input; search results announced |
| [[PKG-date-and-time-picker-with]] | typed input alternative to calendar grid |

<!-- section:at -->
## Assistive technology support matrix

| Combination | Who uses it | Depth per release |
|---|---|---|
| NVDA (current) + Chrome, Windows 11 | counsel, parties, secretariat | full critical journeys |
| JAWS (current and previous major) + Chrome / Edge, Windows 11 (managed) | secretariat, neutrals at institutions | smoke |
| VoiceOver + Safari, macOS | counsel, neutrals | critical journeys |
| VoiceOver + Safari, iOS (current and previous) | parties on phones | critical journeys for `(public)` and `(counsel)` |
| TalkBack + Chrome, Android (current) | parties on phones (largest group in India) | critical journeys for `(public)` and `(counsel)` |
| Windows forced colours (High Contrast) + Edge | low-vision users | smoke on every group |
| Browser zoom 200% and 400%, OS text scaling | low-vision users | every journey page (automated reflow check plus manual sample) |
| Dragon / Windows Voice Access + Chrome | users with motor disabilities | smoke on critical journeys each quarter |
| Keyboard only, Chrome / Firefox / Safari | everyone | every journey, automated in Playwright plus manual |

<!-- section:documents -->
## Documents, media and generated output

Receipts and notices generated for parties are tagged PDF/UA; uploaded documents from the other side may be inaccessible, so each document row has 'Request an accessible copy' which creates an accommodation request ([[APP-accessibility-feedback]]).

<!-- section:tenant -->
## Tenant theming and configuration guardrails

Tenant themes and form-builder forms reach this surface most; their validation is described in [[APP-accessibility-wcag-2-1-aa#tenant]].

<!-- section:testing -->
## Testing method

Sample for this surface (WCAG-EM): sign-in (all methods), invitation acceptance, public filing entry, case list (empty and populated), case overview, Statement of Claim stepper (each step, error summary, upload in progress, infected file, draft conflict, session warning), filing receipt, documents list and viewer, request extension, payment hand-off and return (success, failure), hearing pre-join and room, notifications, profile. Critical journeys run keyboard-only and with TalkBack and VoiceOver iOS on every release.

<!-- section:exceptions -->
## Known exceptions and remediation plan

| Item | Impact | Workaround | Owner | Target date |
|---|---|---|---|---|
| Payment gateway hosted page (vendor) — not yet tested | unknown | assisted payment by secretariat; bank transfer option | finance + accessibility lead | before Phase 5 launch |
| Video provider room UI (if iframe embed) — not yet tested | unknown | phone dial-in; CART link | TERES product | before Phase 4 launch |

<!-- section:reporting -->
## Conformance reporting

Feeds the counsel and public sections of the ACR ([[APP-accessibility-conformance]]) and the evidence pack for SEBI-regulated tenants.

<!-- section:questions -->
## Open questions

- [ ] Which Indian languages are needed at launch for SEBI ODR tenants, and are screen readers tested in them (owner: CORD product)
- [ ] Do we need an assisted-filing route by phone for parties who cannot use the portal (owner: CORD operations)

<!-- checks -->
## Template checks

<!-- check:evidence -->
### Integrity of the conformance claim

The mapping covers all 55 Level A and AA criteria in WCAG 2.2 with method per criterion; the sample includes error, upload, timeout and modal states; 2.5.4 is marked not applicable with reason.

<!-- check:regression -->
### Preventing regression

Playwright keyboard runs for file, pay and request-extension journeys on every PR; axe on every journey state; TalkBack and VoiceOver iOS runs each release.

<!-- check:identity -->
### Authentication and identity verification

3.3.8 is met by paste-friendly OTP, magic link and passkeys; step-up uses the same methods.

<!-- check:due-process -->
### Equal participation in proceedings

Accessible-copy requests from any document row, extension requests from the case, absolute deadlines with time zones, and receipts in tagged PDF support equal participation.

<!-- check:third-party -->
### Third-party and embedded components

Payment and video components are listed as untested exceptions with fallbacks until tested with our AT matrix ([[INT-third-party-component]]).

<!-- end -->
