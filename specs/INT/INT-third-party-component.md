---
id: "INT-third-party-component"
title: "Third-party component accessibility"
parent: "INT-common-integrations"
order: 6
type: "feature"
template: "accessibility"
status: "draft"
owner: null
indicative: false
summary: "Register of embedded vendors (video, e-sign, payments, KYC, chat) with dated ACRs, our own test results and fallback routes"
links: []
rev: 2
syncHash: "1f8fa2b3601e734a"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 9.2.6 Third-party component accessibility

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Register of embedded vendors (video, e-sign, payments, KYC, chat) with dated ACRs, our own test results and fallback routes

<!-- section:scope -->
## Scope and surfaces

Covers every third-party component that a platform user meets **inside or on the way through our journeys**: embedded iframes and SDK widgets, and pages we redirect users to and expect them to complete. In scope:

| Component | Surfaces | Embedding | Personas |
|---|---|---|---|
| Video conferencing room UI / SDK ([[INT-video-conferencing-for-hearings]]) | Hearing room | SDK in our page (option A) or our own UI (option B) | All hearing participants |
| E-sign: Aadhaar eSign ESP authentication page ([[INT-e-signature]]) | Signing journeys | Redirect | Parties, counsel, neutrals in India |
| E-sign: global provider signing session | Signing journeys | Embedded iframe or redirect | Parties, counsel, neutrals |
| Payment gateway hosted checkout ([[BIL-payment-gateway-integration]]) | Case-fee payment, Nomology invoice payment | Redirect or hosted fields iframe | Parties, tenant billing contacts |
| KYC provider capture flows ([[INT-kyc-and-sanctions-screening]]) | Party verification, payee onboarding | Redirect / SDK | Parties, neutrals, transcribers |
| Help or chat widget (if adopted) | All route groups | Script widget | All |
| Bot protection (if adopted) | Public and sign-in surfaces | Script | All |

Out of scope: our own components (covered by [[PKG-design-system-component]]); emails rendered by mail clients; documents uploaded by users ([[DOM-accessible-documents-and]]).

<!-- section:obligations -->
## Standards and legal obligations by jurisdiction

Obligations sit with the tenant or with Nomology depending on region and tenant type, as recorded in [[APP-accessibility-legal-obligations]]; this node does not restate them. Two points specific to third-party components:
- SEBI-regulated tenants must make their digital platforms accessible [R3]; a vendor component inside the journey is part of that platform, so the tenant will ask us for evidence about vendors too. **Assumption, to be confirmed by legal**: we carry the duty to provide evidence and remediation routes for vendors we embed.
- Vendor contracts must carry an accessibility clause (target, remediation time, ACR updates) so we can meet our own commitments; procurement owner: [[SEC-vendor-sub-processor-management]].

<!-- section:target -->
## Conformance target and baseline

Each vendor component must meet **WCAG 2.2 Level AA** [R1] within our journey, the same target as our own surfaces ([[APP-accessibility-wcag-2-1-aa]]). For real-time communication (video), the relevant EN 301 549 clauses for two-way voice and video apply in addition (captions, sign-language video quality) through [[DOM-hearing-room-accessibility]]. Current baseline: **not measured**; vendors are not yet chosen.

<!-- section:criteria -->
## Success criteria mapping

Criteria most often failed by embedded vendor components, and what we test for each (full mapping per vendor in its register entry):

| Criterion | Risk in vendor components | Our test |
|---|---|---|
| 2.1.1 Keyboard, 2.1.2 No Keyboard Trap | iframes that capture focus (payment fields, signing canvas) | Keyboard-only walk-through of the full journey |
| 2.4.3 Focus Order, 2.4.11 Focus Not Obscured | Focus lost when an iframe opens or closes; sticky vendor toolbars | Focus returns to a defined element after each hand-off |
| 3.3.8 Accessible Authentication (Minimum) | OTP entry that blocks paste; CAPTCHAs | Paste and password manager allowed; no puzzle CAPTCHA |
| 2.2.1 Timing Adjustable | Session timeouts on ESP and checkout pages | Timeout length recorded; warning present |
| 1.3.1 Info and Relationships, 4.1.2 Name, Role, Value | Unlabelled fields in hosted forms | Screen reader check of every field |
| 1.4.3 Contrast, 1.4.11 Non-text Contrast | Vendor theming that ignores tenant theme | Contrast measurement in both colour modes |
| 1.4.10 Reflow | Fixed-width iframes on mobile | 320 CSS px width check |
| 2.5.7 Dragging Movements | Signature drawing with mouse only | Typed signature or button alternative |
| 1.2.4 Captions (Live) | Video provider | Live captions available and controllable |
| 3.1.2 Language of Parts | Vendor page language differs from ours | Language matches user choice where vendor supports it |

"Not applicable" must be justified per vendor (for example 1.2.4 for a payment page).

<!-- section:components -->
## Component and pattern requirements

Wrapper components we own around each vendor: `VendorFrame` (labelled iframe with title, focus management on open / close, loading and error states announced through the live region from [[PKG-alerts-toasts-and-status]]), `HandOffNotice` (explains before redirect that the user will leave our site, what the page will ask, and how to come back), and `AlternativeRoute` (link to the fallback route for that vendor).

<!-- section:at -->
## Assistive technology support matrix

Same matrix as the surfaces that host the component ([[APP-party-and-counsel-portal-2]], [[APP-secretariat-console-and-neutral]]): NVDA + Chrome and JAWS + Chrome / Edge on Windows, VoiceOver + Safari on iOS and macOS, TalkBack + Chrome on Android. Vendor flows are tested at "critical journey" depth on all combinations once per vendor release we adopt.

<!-- section:documents -->
## Documents, media and generated output

Vendor output that becomes part of the record: signed PDFs and signing certificates (e-sign), payment receipts (gateway), recordings and captions (video). Signed PDFs must remain tagged if the source was tagged; if the vendor strips tags, we keep the tagged unsigned version alongside as the accessible copy and record the gap. Receipts are regenerated by us as accessible PDFs ([[DOM-accessible-documents-and]]).

<!-- section:tenant -->
## Tenant theming and configuration guardrails

Tenants cannot inject vendor widgets themselves; any widget is added by Nomology after it has a register entry. Tenant theme colours passed to vendors (where vendors accept theming) are validated with the same contrast checks as our themes ([[PKG-tenant-theme-accessibility]]).

<!-- section:testing -->
## Testing method

Per vendor, before adoption and after each vendor release we accept: (1) review of the vendor's ACR (VPAT [R2], noting edition and date; ACRs older than 12 months are treated as unverified), (2) our own expert test of the journey sample — entry, each step, error, timeout, success, cancel — following WCAG-EM sampling [R4], (3) AT testing per the matrix, (4) automated axe checks on our wrapper pages (vendor iframes are often cross-origin and cannot be scanned, so manual testing is mandatory). Results are stored in the register with date, tester, build and vendor version.

<!-- section:exceptions -->
## Known exceptions and remediation plan

Register fields for each known issue: vendor, criterion, impact, workaround, fallback route, vendor ticket, our owner, target date. Known exceptions appear in the ACR and in each tenant's accessibility statement ([[APP-accessibility-conformance]]). Planned fallback routes:

| Vendor | Fallback if inaccessible |
|---|---|
| Payment checkout | Bank transfer with virtual account details on our own accessible page; assisted payment via the secretariat |
| E-sign | Alternative signing method allowed by the tenant (for example global provider instead of ESP, or wet-ink with upload) after a tribunal secretary decision |
| KYC capture | Assisted verification by a trained staff member; document upload instead of liveness ([[PKG-accessible-authentication-and]]) |
| Video | Dial-in audio, interpreter and CART participation through our own room UI |

<!-- section:reporting -->
## Conformance reporting

Register summary feeds the product ACR ([[APP-accessibility-conformance]]) and the SEBI tenant evidence pack ([[RPT-accessibility-audit-evidence-for]]). Owner signs the register review each quarter.

<!-- section:questions -->
## Open questions

- [ ] Legal: confirm our duty to provide accessibility evidence for embedded vendors to regulated tenants.
- [ ] Will any help / chat widget or bot-protection script be used at all? Proposed: none in Phase 5.
- [ ] Accessibility as a scored criterion in each vendor selection (video, e-sign, KYC, gateway): agree weighting with procurement.
- [ ] Who owns the register (accessibility lead or vendor management)?

<!-- checks -->
## Template checks

<!-- check:applicability -->
### Legal applicability and allocation

SEBI-regulated tenants' obligation [R3] extends to embedded components; whether Nomology carries the evidence duty is an open legal question, recorded here as an assumption.

<!-- check:evidence -->
### Integrity of the conformance claim

ACR claims for vendor components are made only from our own stored test records, not from vendor ACRs alone [R2]; vendor ACRs older than 12 months are treated as unverified; the sample follows WCAG-EM [R4] and includes error, timeout and cancel states.

<!-- check:identity -->
### Authentication and identity verification

ESP and KYC flows are checked against 3.3.8 (paste allowed, no puzzle CAPTCHAs) and timing (2.2.1); alternatives to liveness checks are provided through [[PKG-accessible-authentication-and]].

<!-- check:due-process -->
### Equal participation in proceedings

Every vendor has a fallback route so that a party who cannot use the vendor flow can still pay, sign, verify or attend, and the fallback request is routed to the tribunal secretary with its timer so deadlines can be adjusted.

<!-- check:third-party -->
### Third-party and embedded components

This node is the register: every embedded or redirected component is listed with ACR edition and date, our own dated test results against the AT matrix, known issues and a fallback route. Accessibility is a contract term (target, remediation time, ACR refresh) and a selection criterion. Focus traps and obscured focus (2.1.2, 2.4.11) are explicitly tested at each hand-off. Vendor regressions are caught by retesting on each vendor release we adopt and by a quarterly synthetic keyboard run of each critical vendor journey in staging.

<!-- citations -->
## Citations

```json
[
  {
    "body": "W3C",
    "excerpt": "Success criteria at levels A, AA and AAA for accessible web content.",
    "id": "R1",
    "ident": "WCAG",
    "kind": "standard",
    "title": "Web Content Accessibility Guidelines (WCAG) 2.2",
    "url": "https://www.w3.org/TR/WCAG22/",
    "version": "2.2"
  },
  {
    "excerpt": "Template for Accessibility Conformance Reports, with WCAG, Section 508, EN 301 549 and INT editions.",
    "id": "R2",
    "kind": "web",
    "publisher": "Information Technology Industry Council (ITI)",
    "retrieved": "2026-10-28",
    "title": "Voluntary Product Accessibility Template (VPAT)",
    "url": "https://www.itic.org/policy/accessibility/vpat"
  },
  {
    "excerpt": "Requires SEBI-regulated entities to make their digital platforms accessible under the RPwD Act 2016 and rules.",
    "id": "R3",
    "issuer": "Securities and Exchange Board of India",
    "jurisdiction": "India",
    "kind": "regulation",
    "title": "Compliance guidelines for digital accessibility (circular dated 31 July 2025)",
    "url": "https://www.sebi.gov.in/legal/circulars/sep-2025/compliance-guidelines-for-digital-accessibility-circular-rights-of-persons-with-disabilities-act-2016-and-rules-made-thereunder-mandatory-compliance-by-all-regulated-entities-dated-july-31-2025-_96862.html"
  },
  {
    "body": "W3C WAI",
    "excerpt": "Method for defining evaluation scope, sampling pages and states, and reporting conformance.",
    "id": "R4",
    "ident": "WCAG-EM",
    "kind": "standard",
    "title": "WCAG-EM Overview: Website Accessibility Conformance Evaluation Methodology",
    "url": "https://www.w3.org/WAI/test-evaluate/conformance/wcag-em/"
  }
]
```

<!-- end -->
