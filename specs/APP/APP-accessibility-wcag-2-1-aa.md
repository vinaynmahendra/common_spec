---
id: "APP-accessibility-wcag-2-1-aa"
title: "Accessibility (WCAG 2.2 AA)"
parent: "APP-frontend-standards"
order: 1
type: "feature"
template: "accessibility"
status: "draft"
owner: null
indicative: false
summary: "Platform-wide accessibility conformance: WCAG 2.2 Level AA for every persona surface, email and generated document, with the obligations, testing and reporting that make the claim defensible"
links: []
rev: 3
syncHash: "454e1404664cc408"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.4.1 Accessibility (WCAG 2.2 AA)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Platform-wide accessibility conformance: WCAG 2.2 Level AA for every persona surface, email and generated document, with the obligations, testing and reporting that make the claim defensible

<!-- section:scope -->
## Scope and surfaces

Platform-level accessibility node. It sets the single target, shared methods and reporting for everything users interact with:

- All seven route groups of `apps/web` ([[APP-route-groups-per-persona]]), on all tenant hosts, for CORD, TERES and HKIAC CMP tenants
- Transactional emails, SMS and WhatsApp content ([[PKG-notification-copy]])
- Generated documents: receipts, notices, procedural orders, awards, transcripts, eBundles ([[DOM-accessible-documents-and]])
- Live hearings and recordings ([[DOM-hearing-room-accessibility]])
- Embedded third-party components ([[INT-third-party-component]])

Per-surface criteria mappings live in [[APP-party-and-counsel-portal-2]] and [[APP-secretariat-console-and-neutral]]; tenant admin, platform admin, public and transcriber surfaces are mapped in this node until they get their own nodes. Obligations are detailed in [[APP-accessibility-legal-obligations]], reports in [[APP-accessibility-conformance]], feedback in [[APP-accessibility-feedback]].

Out of scope: documents uploaded by parties (third-party content, see Documents section); the marketing website.

The node ID still says 2.1; the target is WCAG 2.2.

<!-- section:obligations -->
## Standards and legal obligations by jurisdiction

Summary; the register with instruments, obligated party and contract clause is [[APP-accessibility-legal-obligations]] and must be signed off by legal.

| Region / tenant type | Main instruments (status) | Obligated party | Standard pointed to |
|---|---|---|---|
| India, private institutions (arbitral institutions, CORD clients) | RPwD Act 2016 s.46 service providers [R1] (in force) | tenant as service provider; Nomology by contract | per RPwD Rules; assumption: GIGW / IS 17802 by reference, to be confirmed by legal |
| India, SEBI-regulated entities and MIIs, and ODR institutions serving them | SEBI digital accessibility circular of 31 July 2025 [R2] (in force; applicability to ODR institutions to be confirmed) | regulated entity; passed to Nomology by contract | as stated in the circular, to be confirmed |
| India, government or court tenants | GIGW 3.0 [R3], RPwD Act | tenant | GIGW 3.0 (WCAG-based) |
| United States, state or local government tenants | ADA Title II web rule (2024) | tenant | WCAG 2.1 AA (2.2 AA exceeds it) |
| United States, federal procurement | Section 508 | tenant / Nomology when selling | Revised 508 Standards (WCAG 2.0 AA) |
| Singapore | Assumption: no general statutory web accessibility duty on private institutions; contract-driven | by contract | WCAG 2.2 AA by our standard |
| EU users of any tenant | European Accessibility Act applicability not assumed; counsel to confirm | — | EN 301 549 |

<!-- section:target -->
## Conformance target and baseline

- **Target**: WCAG 2.2 Level AA [R4] for every surface in scope, all success criteria at Levels A and AA.
- **Additional clauses**: EN 301 549 [R5] (and its Indian counterpart IS 17802, assumption to confirm) clause 6 (ICT with two-way voice communication) for the hearing room, clause 10 (non-web documents) for generated PDFs, clause 11 where software-like behaviour applies (editors, viewer).
- **Documents we generate**: PDF/UA-1 tagged PDFs.
- **Selected AAA practices** adopted where they cost little and help our users (not claimed): 2.2.6 timeouts warning text, 3.1.5 reading level guidance for party journeys ([[DOC-plain-language-guidance-for]]), 2.4.13 focus appearance via tokens.
- **Baseline**: no measured baseline yet (new platform). First baseline: expert audit of the Phase 3 vertical slice (counsel portal and secretariat console) against WCAG-EM.

<!-- section:criteria -->
## Success criteria mapping

Criteria owned at platform level (met by shared mechanisms, inherited by every surface):

| Criterion | Met by | How | Proved by |
|---|---|---|---|
| 1.2.2, 1.2.4 Captions (prerecorded, live) | hearing room and recordings | live captions / CART and captioned recordings ([[DOM-hearing-room-accessibility]]) | manual AT test per release |
| 1.3.1, 4.1.2 | design-system components ([[PKG-design-system-component]]) | APG patterns, semantic HTML | axe on Storybook; manual review |
| 1.4.3, 1.4.11 contrast | tokens and tenant theme validation ([[PKG-colour-and-contrast]], [[PKG-tenant-theme-accessibility]]) | contrast-pair manifest; activation blocked on failure | CI contrast check |
| 1.4.10 Reflow, 1.4.4 Resize | [[APP-responsive-mobile-first]] | RESP-3 | Playwright overflow check |
| 2.2.1 Timing Adjustable | session warning in every layout | warn 2 min before idle timeout with extend | Playwright test |
| 2.4.1 Bypass Blocks | every layout | skip link to `#main`, landmarks | axe + manual |
| 2.4.2 Page Titled | every page `generateMetadata` | "{Page} – {Case ref} – {Tenant}" | lint + Playwright |
| 2.4.7, 2.4.11 Focus | tokens; sticky header offset (`scroll-padding-top`) | non-tenant-overridable focus ring | visual + manual |
| 3.1.1, 3.1.2 Language | root layout `lang`, `lang` on mixed-language titles | | Playwright |
| 3.2.3, 3.2.4 Consistency | persona shells | same nav and labels across pages | review |
| 3.2.6 Consistent Help | every layout | "Help" in the same place: help centre and accessibility contact | review |
| 3.3.8 Accessible Authentication | [[APP-public-and-sign-in-surfaces]], [[PKG-accessible-authentication-and]] | paste, password managers, magic link, passkeys, no puzzles | manual + Playwright |
| 4.1.3 Status Messages | [[PKG-alerts-toasts-and-status]] | live regions | manual AT |

Surface mappings: `(counsel)` and `(public)` in [[APP-party-and-counsel-portal-2]]; `(secretariat)` and `(neutral)` in [[APP-secretariat-console-and-neutral]]; `(transcriber)`, `(tenant-admin)` and `(platform-admin)` inherit the counsel mapping for shared components plus surface notes in their frontend nodes until they get their own mapping (gap; see questions).

<!-- section:components -->
## Component and pattern requirements

All shared components carry an accessibility contract (ARIA pattern, keyboard model, announcements, target size) in [[PKG-design-system-component]], checked on Storybook stories in CI. Pages may not re-implement these patterns ([[APP-frontend-standards]] FE-1).

<!-- section:at -->
## Assistive technology support matrix

| Combination | Who uses it | Depth per release |
|---|---|---|
| NVDA (current) + Chrome, Windows 11 | counsel, parties, secretariat | full critical journeys |
| JAWS (current and previous major) + Chrome / Edge, Windows 11 (managed) | secretariat, neutrals at institutions | full critical journeys for secretariat and neutral; smoke for others |
| VoiceOver + Safari, macOS | counsel, neutrals | critical journeys |
| VoiceOver + Safari, iOS (current and previous) | parties on phones | critical journeys for `(public)` and `(counsel)` |
| TalkBack + Chrome, Android (current) | parties on phones (largest group in India) | critical journeys for `(public)` and `(counsel)` |
| Windows forced colours (High Contrast) + Edge | low-vision users | smoke on every group |
| Browser zoom 200% and 400%, OS text scaling | low-vision users | every journey page (automated reflow check plus manual sample) |
| Dragon / Windows Voice Access + Chrome | users with motor disabilities | smoke on critical journeys each quarter |
| Keyboard only, Chrome / Firefox / Safari | everyone | every journey, automated in Playwright plus manual |

<!-- section:documents -->
## Documents, media and generated output

| Content | Platform guarantee |
|---|---|
| Generated receipts, notices, procedural orders, awards, transcripts | Tagged PDF/UA-1 from structured sources, with language, headings, reading order and bookmarks ([[DOM-accessible-documents-and]]) |
| eBundles | Bookmarked per document and section, page labels matching bundle pagination, OCR text layer on scanned pages; tags for generated index pages |
| Uploaded documents by parties | Not guaranteed (third-party content). OCR layer added; accessible-copy request route ([[APP-accessibility-feedback]]); notice on untagged files |
| Hearing recordings | Captions within the transcript turnaround; transcript as accessible PDF and WebVTT |
| Live hearings | Live captions or CART on request, sign-language interpreter pinning ([[DOM-hearing-room-accessibility]]) |
| AI-generated text | Labelled; same structure rules; counted as conformant only after human review ([[AI-ai-generated-text-labelling-and]]) |
| Emails | Semantic HTML, plain-text part, no image-only content, link text meaningful ([[PKG-notification-copy]]) |

<!-- section:tenant -->
## Tenant theming and configuration guardrails

- Themes: contrast and focus checks at save; activation blocked on failure; checked in light, dark, high contrast and 400% zoom ([[PKG-tenant-theme-accessibility]]).
- Form-builder forms: every field must have a label; hints and errors use the shared components; heading order validated ([[PKG-forms-and-form-builder]]).
- Tenant copy and rich text: sanitised to a structure allow-list; links need text; images need alt text ([[PKG-tenant-terminology-and-copy]]).
- Document templates uploaded by tenants (for example an institution's award template): validated for tagging capability; untagged output blocks activation unless the tenant accepts an exception recorded in its accessibility statement.
- No tenant custom CSS or scripts.

<!-- section:testing -->
## Testing method

Following WCAG-EM [R6]:
1. **Automated** on every PR: axe-core on Storybook stories and on every Playwright journey state; `eslint-plugin-jsx-a11y`; contrast manifest; reflow check. Serious and critical axe findings fail the build.
2. **Manual expert review** of every applicable criterion on the sample each release with UI changes, and a full audit twice a year.
3. **AT testing** per the matrix above.
4. **Testing with disabled users** at least twice a year, covering screen-reader, low-vision, motor and cognitive disabilities, in English and at least one Indian language [R7].
5. **Sample** (per WCAG-EM): sign-in, invitation acceptance, case list, case overview, file a Statement of Claim (all steps, error state, upload states), document view, pay, request extension, hearing pre-join and room, secretariat queue and bulk action, scheduling, award editor, transcript editor, theme editor, plus errors, empty states, timeouts and modals.

<!-- section:exceptions -->
## Known exceptions and remediation plan

Known exceptions are listed per surface in the surface nodes and summarised in the ACR. At platform level: none recorded yet (pre-launch). Expected risk areas: third-party video, payment and e-sign components ([[INT-third-party-component]]); rich-text editor accessibility.

<!-- section:reporting -->
## Conformance reporting

Feeds the ACR per product release (VPAT INT edition) and per-tenant accessibility statements ([[APP-accessibility-conformance]]), and the audit evidence pack for SEBI-regulated tenants ([[RPT-accessibility-audit-evidence-for]]).

<!-- section:support -->
## Feedback, accommodation and grievance

Report-a-barrier and accommodation requests are handled by [[APP-accessibility-feedback]]; a 'Report an accessibility problem' link is part of the consistent help location on every page.

<!-- section:questions -->
## Open questions

- [ ] Legal confirmation of the instruments and standards in the obligations summary, especially the RPwD Rules standard by reference and the SEBI circular's reach to ODR institutions (owner: legal)
- [ ] Separate criteria mappings for `(transcriber)`, `(tenant-admin)` and `(platform-admin)` (owner: accessibility lead)
- [ ] Who is the accessibility lead and ACR signatory? (owner: CTO)
- [ ] Is IS 17802 the right Indian reference for documents and real-time communication clauses? (owner: legal / accessibility lead)
- [ ] Rename node ID to reflect WCAG 2.2 (owner: workspace admin)

<!-- checks -->
## Template checks

<!-- check:applicability -->
### Legal applicability and allocation

Tenant type (government, SEBI-regulated or serving SEBI matters, private institution) is to be recorded per tenant in tenant settings and drives which instruments apply; the MSA states the WCAG 2.2 AA target and remediation times. The instrument list and its draft status are maintained in [[APP-accessibility-legal-obligations]], which needs legal sign-off.

<!-- check:evidence -->
### Integrity of the conformance claim

Each ACR row will link to stored test records (date, tester, method, AT, build SHA) from the testing pipeline; the sample includes error, empty, timeout and modal states; 'Partially supports' entries describe the user impact and the workaround.

<!-- check:tenancy -->
### Tenant customisation and content

Themes, forms, copy and document templates are validated at save time and cannot be activated when they fail; no tenant CSS or scripts; tenant statements are generated from tenant configuration and contacts.

<!-- check:regression -->
### Preventing regression

axe on Storybook and Playwright journey states with serious and critical findings failing the build; jsx-a11y lint; keyboard Playwright tests for file, pay, accept appointment, submit award; accessibility in the Definition of Done; full manual audit twice a year and after major redesigns.

<!-- check:identity -->
### Authentication and identity verification

Sign-in meets 3.3.8 with paste, password managers, magic link and passkeys; OTPs last 10 minutes with resend; no puzzle CAPTCHAs; alternatives to liveness checks are specified in [[PKG-accessible-authentication-and]].

<!-- check:due-process -->
### Equal participation in proceedings

Accommodation requests (accessible copy, extension, interpreter, CART) are raised from within the case and routed to the tribunal secretary as procedural requests with timers ([[APP-accessibility-feedback]]); deadlines are shown as absolute dates with time zones.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "issuer": "Government of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 49 of 2016",
    "title": "Rights of Persons with Disabilities Act, 2016",
    "url": "https://indiacode.nic.in/bitstream/123456789/15939/1/the_rights_of_persons_with_disabilities_act%2C_2016.pdf"
  },
  {
    "id": "R2",
    "issuer": "SEBI",
    "jurisdiction": "India",
    "kind": "regulation",
    "title": "Compliance guidelines for digital accessibility (circular dated 31 July 2025)",
    "url": "https://www.sebi.gov.in/legal/circulars/sep-2025/compliance-guidelines-for-digital-accessibility-circular-rights-of-persons-with-disabilities-act-2016-and-rules-made-thereunder-mandatory-compliance-by-all-regulated-entities-dated-july-31-2025-_96862.html"
  },
  {
    "body": "Government of India",
    "id": "R3",
    "ident": "GIGW 3.0",
    "kind": "standard",
    "title": "Guidelines for Indian Government Websites and Apps: scope and objective",
    "url": "https://guidelines.india.gov.in/scope-and-objective/"
  },
  {
    "body": "W3C",
    "id": "R4",
    "ident": "WCAG 2.2",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "W3C Recommendation"
  },
  {
    "body": "ETSI",
    "id": "R5",
    "ident": "EN 301 549",
    "kind": "standard",
    "title": "Accessibility requirements for ICT products and services",
    "url": "https://www.etsi.org/deliver/etsi_en/301500_301599/301549/03.02.01_60/en_301549v030201p.pdf",
    "version": "V3.2.1 (2021-03)"
  },
  {
    "body": "W3C WAI",
    "id": "R6",
    "ident": "WCAG-EM",
    "kind": "standard",
    "title": "WCAG-EM Overview: Website Accessibility Conformance Evaluation Methodology",
    "url": "https://www.w3.org/WAI/test-evaluate/conformance/wcag-em/"
  },
  {
    "body": "W3C WAI",
    "id": "R7",
    "kind": "standard",
    "title": "Involving Users in Evaluating Web Accessibility",
    "url": "https://www.w3.org/WAI/test-evaluate/involving-users/"
  }
]
```

<!-- end -->
