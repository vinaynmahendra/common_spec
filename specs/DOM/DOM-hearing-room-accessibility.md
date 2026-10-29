---
id: "DOM-hearing-room-accessibility"
title: "Hearing room accessibility"
parent: "DOM-hearings"
order: 2
type: "feature"
template: "accessibility"
status: "draft"
owner: null
indicative: false
summary: "Live captions / CART, sign-language interpreter pinning, keyboard control, accessible chat (EN 301 549 / IS 17802 real-time communication clauses)"
links: []
rev: 2
syncHash: "639e2c8ace00c46b"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 6.4.2 Hearing room accessibility

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Live captions / CART, sign-language interpreter pinning, keyboard control, accessible chat (EN 301 549 / IS 17802 real-time communication clauses)

<!-- section:scope -->
## Scope and surfaces

This node covers accessibility of **live hearings** on the platform:

- The in-browser hearing room ([[APP-hearing-room-in-browser]]): pre-join device check, waiting room, main room, party breakout rooms, controls (microphone, camera, hand, chat, leave), participant list, document presentation ("follow the presenter") and recording indicator.
- Embedded third-party video components from [[INT-video-conferencing-for-hearings]] (SDK or iframe), including their captions and controls.
- Live captions (machine ASR) and human CART (communication access real-time translation), sign-language interpreter pinning and spotlight, spoken-language interpreter channels.
- Accessible chat and hand-raise queue.
- Phone dial-in and audio-only modes as alternatives.
- Hearing-related emails and calendar invites are covered by [[APP-accessibility-wcag-2-1-aa]]; recordings and transcripts after the hearing by [[DOM-accessible-documents-and]].

**Out of scope**: scheduling screens (covered by [[APP-secretariat-console-and-neutral]] and [[APP-party-and-counsel-portal-2]]); physical venue accessibility (tenant responsibility, recorded on the venue as `accessibility_features`).

<!-- section:obligations -->
## Standards and legal obligations by jurisdiction

**Draft for legal sign-off.**

| Region / tenant type | Instrument | Who carries it | Points to |
|---|---|---|---|
| India, all tenants | Rights of Persons with Disabilities Act, 2016 [R1]: accessibility of services by service providers | Tenant (institution) as service provider; Nomology by contract | Accessibility standards notified under the Act (IS 17802, aligned with EN 301 549) – applicability to private ODR / arbitration services to be confirmed by legal |
| India, SEBI-regulated tenants and MIIs | SEBI digital accessibility circular of 31 July 2025 [R2] | Regulated entity; flows down to us as a supplier | WCAG 2.x AA plus audit evidence ([[RPT-accessibility-audit-evidence-for]]) – whether ODR institutions are directly covered to be confirmed |
| All, due process | Equal treatment of parties and a full opportunity to present the case (India: Arbitration and Conciliation Act s.18 [R3]; similar in institution rules) | Tribunal and institution | Not a technical standard; drives accommodations below |
| EU-connected tenants | EN 301 549 chapter 6 (ICT with two-way voice communication) [R4] | Tenant if covered by the European Accessibility Act – not assumed | EN 301 549 |
| US tenants | ADA (Title II for public bodies, Title III exposure to be assessed) | Tenant | WCAG 2.1 AA under the Title II rule for public bodies; others by contract |
| Singapore | No specific statutory web accessibility mandate identified for private institutions (assumption; legal to confirm) | By contract | Platform target |

The platform target applies to all tenants regardless of their legal minimum.

<!-- section:target -->
## Conformance target and baseline

- **WCAG 2.2 Level AA** for all hearing-room web content [R5].
- **EN 301 549 V3.2.1 chapter 6** real-time communication clauses, applied through the IS 17802 equivalent in India [R4]: where the room offers video, it supports sign-language communication with adequate resolution, frame rate and audio-video synchronisation (exact thresholds to be taken from the clause text and verified against V4.1.1 [R6]); real-time text (chat) usable alongside voice; caption display that can be turned on and off.
- **Live captions** (WCAG 1.2.4) for every recorded or tribunal-directed hearing in the language of the hearing, by machine ASR at minimum and by human CART when requested as an accommodation.
- Baseline: not yet measured; first audit planned with the Phase 4 hearing room release.

<!-- section:criteria -->
## Success criteria mapping

| Criterion | Where met | How | Test |
|---|---|---|---|
| 1.2.4 Captions (Live) AA | Caption panel | ASR captions streamed from the in-region ASR service; CART feed embedded when booked | Manual review in each language; CART integration test |
| 1.3.1 Info and Relationships A | Participant list, chat, hand queue | Lists and live regions with names and roles | axe + screen reader walk-through |
| 1.4.3 Contrast (Minimum) AA / 1.4.11 Non-text Contrast AA | Controls, recording indicator, speaking indicator | Design tokens ([[PKG-colour-and-contrast]]) | Contrast manifest in CI |
| 1.4.10 Reflow AA | Room layout | Single-column layout at 320 CSS px with video, captions and controls stacked | Playwright at 320 px |
| 1.4.13 Content on Hover or Focus AA | Control tooltips | Dismissible, hoverable, persistent | Manual |
| 2.1.1 Keyboard A / 2.1.2 No Keyboard Trap A | All controls, including provider SDK controls | Our own control bar over the SDK; keyboard shortcuts documented and remappable | Keyboard-only E2E per journey |
| 2.1.4 Character Key Shortcuts A | Mute / camera shortcuts | Shortcuts use a modifier or can be turned off | Manual |
| 2.2.1 Timing Adjustable A | Waiting room, idle disconnect | No automatic removal for inactivity during a session; idle warning with extend | Manual |
| 2.3.1 Three Flashes A | Video tiles, screen share | Platform UI has no flashing; shared content is outside our control, noted as a limitation | Manual |
| 2.4.3 Focus Order A / 2.4.11 Focus Not Obscured (Minimum) AA | Room with overlays (captions, chat) | Overlays do not cover the focused control; focus returns after dialogs | Manual + Playwright |
| 2.5.8 Target Size (Minimum) AA | Control bar | Minimum 24 by 24 CSS px, controls 44 px on touch | Automated check on stories |
| 3.2.2 On Input A | Device selection | No context change on selection without confirmation | Manual |
| 3.3.8 Accessible Authentication (Minimum) AA | Join, guest token | Magic link or one-time code with paste allowed, no CAPTCHA | [[PKG-accessible-authentication-and]] tests |
| 4.1.2 Name, Role, Value A | Every control incl. toggles | `aria-pressed` on toggles, accessible names include state ("Microphone on") | axe + NVDA / VoiceOver |
| 4.1.3 Status Messages AA | Join / leave, hand raised, recording started, you were admitted, connection lost | Polite live region; recording start is assertive | Screen reader test |

Not applicable with reason: 1.2.3 / 1.2.5 audio description apply to prerecorded media and are covered by [[DOM-accessible-documents-and]] for recordings.

<!-- section:components -->
## Component and pattern requirements

| Component | Accessibility contract |
|---|---|
| Control bar (custom, wraps the provider SDK) | Toolbar pattern ([[PKG-design-system-component]]): arrow keys within, Tab in and out; toggle buttons expose state |
| Video tile grid | Each tile labelled with participant name and role; speaking state announced only on request (no constant announcements); spotlight and pin actions on each tile via a menu button |
| Interpreter pin | Secretariat and the participant can pin a sign-language interpreter tile so it stays visible at a minimum size in every layout, including screen share |
| Caption panel | Resizable text, font size up to 200%, position top or bottom, high-contrast option, speaker names, scroll-back of the last 15 minutes |
| Chat | Log pattern with live region for new messages (politeness configurable), message composer with label, no time-out |
| Hand queue | Ordered list, own position announced on change |
| Dialogs (leave, admit witness) | [[PKG-modal-dialog-and-consequential]] |
| Toasts | [[PKG-alerts-toasts-and-status]] |

<!-- section:at -->
## Assistive technology support matrix

| Persona and setting | Browser + AT | Depth |
|---|---|---|
| Counsel and neutrals on desktop | Chrome + NVDA (Windows); Edge + JAWS (Windows); Safari + VoiceOver (macOS) | Full journey every release |
| Secretariat on managed Windows | Edge or Chrome + JAWS | Full journey every release |
| Parties on mobile | Safari + VoiceOver (iOS); Chrome + TalkBack (Android) | Join, mute, captions, chat, leave every release |
| Low vision | Windows high-contrast / forced colours; browser zoom 200% and 400% | Every release |
| Deaf or hard of hearing | Captions on, interpreter pinned | Every release |
| Keyboard only | Chrome, Firefox | Every release |

<!-- section:documents -->
## Documents, media and generated output

During a hearing, documents shown through "follow the presenter" use the platform document viewer ([[APP-document-viewer-and-sandbox]]) rather than video screen share where possible, so that screen-reader users can read the same page in text with the page reference announced. Screen share of third-party content is not guaranteed accessible; the presenter is prompted to share the bundle page reference so others can open it in the viewer. Live captions are not a transcript; after the hearing, captions are not kept unless the tribunal directs, and the certified transcript comes from [[DOM-transcribers]].

<!-- section:tenant -->
## Tenant theming and configuration guardrails

Tenants cannot change the control layout, colours of controls, or caption styling defaults below the platform minimum. Tenant branding affects only the waiting-room header and uses validated themes ([[PKG-tenant-theme-accessibility]]). Tenant settings that affect accessibility (recording default, waiting room, CART provider) are listed in the tenant admin console with a note when a choice affects accommodations.

<!-- section:testing -->
## Testing method

- Automated: axe rules on Storybook stories for every hearing-room component and on Playwright journey states (join, in room, breakout, captions on, interpreter pinned, reconnecting); build fails on serious or critical issues.
- Manual expert review against every criterion in the mapping each major release, following WCAG-EM sampling [R7]: pre-join, waiting room, main room with 2, 9 and 25 participants, breakout room, screen share, reconnection, leave.
- AT testing per the matrix.
- Testing with disabled users: at least one session per half-year with Deaf, blind and motor-impaired participants in a mock hearing (paid, with consent).
- Provider SDK regressions: a smoke test suite runs against each new provider SDK version before upgrade.

<!-- section:exceptions -->
## Known exceptions and remediation plan

| Known gap | Impact | Workaround | Owner | Target |
|---|---|---|---|---|
| Provider SDK controls not fully keyboard accessible (to be verified per provider) | Keyboard users cannot reach some provider controls | Our own control bar replaces provider controls | Hearing room team | Before Phase 4 release |
| ASR captions in some Indian languages not available or low quality | Deaf participants in those hearings | Human CART or interpreter booked as an accommodation | Product | Ongoing |
| Shared screen content may be inaccessible | Screen-reader users cannot read shared slides | Presenter prompted to use document viewer | Product | Ongoing |

<!-- section:reporting -->
## Conformance reporting

Feeds the hearing-room section of the platform ACR (VPAT INT edition) via [[APP-accessibility-conformance]], with chapter 6 rows from EN 301 549 / IS 17802. Re-issued each release that changes the room. SEBI-regulated tenants receive the evidence pack through [[RPT-accessibility-audit-evidence-for]].

<!-- section:support -->
## Feedback, accommodation and grievance

Accommodation requests (CART, sign-language interpreter, extra breaks, audio-only participation, pre-hearing room test) are raised from the case or the hearing notice and routed to the tribunal secretary through [[APP-accessibility-feedback]] as a human task with a response target (proposed 3 business days, or 1 business day if the hearing is within 7 days). Approved accommodations attach to the participant on every session (HRG-BR-13). A "report a barrier" control is available inside the room and does not leave the hearing.

<!-- section:questions -->
## Open questions

- [ ] Which video providers in each region offer an SDK that lets us replace all controls and pin tiles? Drives the exception list. Owner: integrations.
- [ ] CART provider(s) per region and how their feed is embedded (iframe vs caption stream API).
- [ ] Legal: confirm whether RPwD s.46 duties and the SEBI 2025 circular reach ODR institutions and private arbitral institutions directly, or only through contract.
- [ ] Should live captions be retained as an interim aid until the certified transcript is delivered? Needs tribunal and privacy view.

<!-- checks -->
## Template checks

<!-- check:applicability -->
### Legal applicability and allocation

Duties per tenant type are in the obligations table (draft for legal). Tenant type (MII / SEBI-regulated, private institution, CORD) is recorded in tenant settings so the right evidence pack applies. The MSA will state WCAG 2.2 AA plus EN 301 549 chapter 6 for the hearing room, defect response times and who pays for regulator-required third-party audits. Instruments still unconfirmed (SEBI coverage of ODR institutions, EN 301 549 V4.1.1 adoption) are open questions with legal as owner.

<!-- check:regression -->
### Preventing regression

Axe on every hearing-room story and journey state blocks the build on serious issues; keyboard-only Playwright journeys (join, mute, raise hand, chat, pin interpreter, leave) run on every pull request touching the room; the provider SDK smoke suite runs on version bumps; a full manual audit is repeated each major release.

<!-- check:due-process -->
### Equal participation in proceedings

Accommodations are requested in-case and routed to the tribunal secretary as a procedural request with a timer; approved accommodations follow the participant to every session. Interpreter pinning, live captions and CART, and keyboard control are built in. Hearing notices show absolute date and time in the participant's own time zone. The basis is the tribunal's duty to treat parties equally and give each a full opportunity to present their case [R3].

<!-- check:third-party -->
### Third-party and embedded components

The video provider is the main third-party dependency. We wrap it with our own control bar and tile layout so keyboard and screen-reader behaviour is ours, test each provider SDK version before upgrade, and record provider ACRs and our own test results in [[INT-third-party-component]]. Phone dial-in and audio-only are the fallback when the room fails for a participant.

<!-- check:feedback -->
### People with disabilities in the loop

An in-room "report a barrier" control and the accommodation channel route to the tenant's nodal officer and tribunal secretary. Proposed target: acknowledge within 1 business day; issues classified by WCAG criterion and added to the exceptions list. Mock hearings with disabled participants twice a year.

<!-- citations -->
## Citations

```json
[
  {
    "clause": "s.46",
    "excerpt": "Section 46 requires service providers, whether government or private, to provide services in accordance with the accessibility rules made under the Act.",
    "id": "R1",
    "issuer": "Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 49 of 2016",
    "title": "Rights of Persons with Disabilities Act, 2016",
    "url": "https://indiacode.nic.in/bitstream/123456789/15939/1/the_rights_of_persons_with_disabilities_act%2C_2016.pdf"
  },
  {
    "excerpt": "Digital accessibility compliance guidelines for SEBI-regulated entities.",
    "id": "R2",
    "issuer": "Securities and Exchange Board of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "SEBI circular, 31 July 2025",
    "title": "Compliance guidelines for digital accessibility (circular dated 31 July 2025)",
    "url": "https://www.sebi.gov.in/legal/circulars/sep-2025/compliance-guidelines-for-digital-accessibility-circular-rights-of-persons-with-disabilities-act-2016-and-rules-made-thereunder-mandatory-compliance-by-all-regulated-entities-dated-july-31-2025-_96862.html"
  },
  {
    "clause": "s.18",
    "excerpt": "Section 18: the parties shall be treated with equality and each party shall be given a full opportunity to present the case.",
    "id": "R3",
    "issuer": "Government of India (Ministry of Law and Justice)",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 26 of 1996",
    "title": "The Arbitration and Conciliation Act, 1996",
    "url": "https://www.indiacode.nic.in/bitstream/123456789/1978/1/A199626.pdf"
  },
  {
    "body": "ETSI",
    "clause": "Chapter 6",
    "excerpt": "Chapter 6 sets requirements for ICT with two-way voice communication, including real-time text and video communication supporting sign language.",
    "id": "R4",
    "ident": "EN 301 549",
    "kind": "standard",
    "title": "ETSI EN 301 549 V3.2.1 Accessibility requirements for ICT products and services",
    "url": "https://www.etsi.org/deliver/etsi_en/301500_301599/301549/03.02.01_60/en_301549v030201p.pdf",
    "version": "V3.2.1 (2021-03)"
  },
  {
    "body": "W3C",
    "clause": "1.2.4",
    "excerpt": "Success criterion 1.2.4 requires captions for all live audio content in synchronised media (Level AA).",
    "id": "R5",
    "ident": "WCAG 2.2",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "2.2"
  },
  {
    "body": "ETSI",
    "clause": "Chapter 6",
    "excerpt": "Latest published version of EN 301 549; clause thresholds to be verified against it.",
    "id": "R6",
    "ident": "EN 301 549",
    "kind": "standard",
    "title": "ETSI EN 301 549 V4.1.1 Accessibility requirements for ICT products and services",
    "url": "https://www.etsi.org/deliver/etsi_en/301500_301599/301549/04.01.01_60/en_301549v040101p.pdf",
    "version": "V4.1.1 (2026-09)"
  },
  {
    "body": "W3C WAI",
    "excerpt": "Methodology for sampling and evaluating conformance of a website to WCAG.",
    "id": "R7",
    "ident": "WCAG-EM",
    "kind": "standard",
    "title": "WCAG-EM Overview: Website Accessibility Conformance Evaluation Methodology",
    "url": "https://www.w3.org/WAI/test-evaluate/conformance/wcag-em/"
  }
]
```

<!-- end -->
