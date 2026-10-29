# Template: Accessibility conformance (`accessibility`)

Generated from `accessibility.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies what accessibility standard a surface or the whole platform must meet, which laws and contracts require it in each region, how conformance is tested and how it is reported, so that conformance claims are accurate and defensible.

**Depth:** 3–8 pages. The obligations table, success-criteria mapping and AT matrix must be complete for the stated scope; partial mappings are how false conformance claims happen. Legal statements must cite the instrument and be signed off by legal; mark drafts. Split by surface when the criteria mapping exceeds about 40 rows, keeping one platform-level node for obligations and reporting.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `scope` Scope and surfaces (level 1)

Name exactly what this conformance node covers: which apps, route groups, personas, emails, documents and media, and what is deliberately out of scope. A conformance claim is only as good as its stated scope.

Illustrative example (not a requirement):

> **In scope:** party / counsel route group `(party)` — sign-in, case overview, filing journey, payments hand-off, receipts; transactional emails sent from these journeys; filing receipts (PDF).
> 
> **Out of scope here (own nodes):** hearing room (see *Hearing room accessibility*), eBundle PDFs (see *Accessible documents*), tenant admin console.
> 
> | Surface | Personas | Entry points | Pages sampled |
> |---|---|---|---|
> | `(party)` web app | Claimant, respondent, counsel | Invitation email, tenant subdomain | 14 templates, 31 states |
> | Transactional email | Same | n/a | 9 templates |
> | Filing receipt PDF | Same | Download, email attachment | 1 template |

### `obligations` Standards and legal obligations by jurisdiction (level 1)

For each region and tenant type this surface serves, list the laws, regulator directions and contract terms that apply, who carries the obligation (Nomology, the tenant, or both), and the standard each one points to. Mark anything in draft or unconfirmed, and get legal sign-off.

Illustrative example (not a requirement):

> | Jurisdiction / source | Applies when | Standard referenced | Obligated party | Status |
> |---|---|---|---|---|
> | India — RPwD Act 2016 s.40 (standards), s.46 (service providers, public or private); penalties s.89 | Any India-region tenant; any service offered to people in India | Rule 15(1)(c) RPwD Rules 2017: GIGW for websites, ePUB / OCR-based PDF for documents, IS 17802 Parts 1–2 for ICT | Tenant as service provider; Nomology as supplier by contract | In force. SC in *Rajive Raturi* (8 Nov 2024) held Rule 15(1) ultra vires and directed mandatory rules |
> | India — draft RPwD (Amendment) Rules 2026 (S.O. 3962(E), 16 Jul 2026, per secondary sources) | Establishments making websites, apps, e-documents available in India | IS 17802; mandatory Accessibility Conformance Report, human- and machine-readable | Establishment; supplier ACR must be verified | **Draft — confirm final text in Gazette** |
> | India — SEBI circular 31 Jul 2025 + compliance guidelines (Sep 2025) | SEBI-regulated entities incl. MIIs (e.g. NSE) whose platforms we power | IS 17802, WCAG 2.1 or later, annual audit by IAAP-certified auditor | MII / RE; we supply evidence | In force; **confirm whether ODR-institution tenants are themselves in scope** |
> | India — GIGW 3.0 | Government tenants (e.g. a High Court, consumer commission) | GIGW 3.0 (WCAG 2.1 AA based) | Government body; us by contract | In force for government sites |
> | US — ADA Title II rule (28 CFR 35.200) | State / local government tenants | WCAG 2.1 AA; compliance April 2027 / April 2028 after 2026 interim final rule | Public entity | In force |
> | US — Section 508 | Federal agency procurement | Revised 508 (incorporates WCAG 2.0 AA) | Agency; we supply ACR | In force |
> | EU — European Accessibility Act | Only if a tenant offers an in-scope consumer service in the EU | EN 301 549 | Service provider | **Likely out of scope for B2B ODR — confirm** |
> | Singapore, Hong Kong | Contract only (HK Disability Discrimination Ordinance covers services generally) | WCAG 2.2 AA by contract | Per contract | No specific private-sector web statute identified — confirm with counsel |

### `target` Conformance target and baseline (level 1)

State the single target the surface must meet (version and level), the extra clauses beyond WCAG that apply (for example EN 301 549 / IS 17802 clauses for documents, software and real-time communication), and the current measured baseline.

Illustrative example (not a requirement):

> - **Target:** WCAG 2.2 Level AA for all in-scope pages and states. Because WCAG 2.2 AA is a superset of 2.1 AA, this also meets SEBI's "WCAG 2.1 or later" and the ADA Title II rule.
> - **Additional clauses:** IS 17802-1 / EN 301 549 clause 10 (non-web documents) for receipts and awards; clause 6 (real-time communication) for hearing chat; clause 11 where a desktop helper app exists.
> - **Selected AAA / beyond-AA goals (not claimed):** 2.4.13 Focus Appearance, plain-language summaries per COGA guidance.
> - **Baseline (audit of 12 Oct):** 41 failures across 9 success criteria; 3 blockers (1.3.1 on case table, 2.1.1 on bundle reorder, 4.1.2 on custom date picker).

### `criteria` Success criteria mapping (level 1)

Map every success criterion that is relevant to this surface to where it is met (design system component, page, content rule), how, and which test proves it. Mark criteria that do not apply with a reason; "not applicable" must be justified, not assumed.

Illustrative example (not a requirement):

> | SC | Where it bites | How it is met | Verified by |
> |---|---|---|---|
> | 1.3.1 Info and Relationships | Case list table, filing form fieldsets | Native `<table>` with `<th scope>`; `<fieldset>`/`<legend>` for document-type radios | axe in CI + manual NVDA pass |
> | 2.4.11 Focus Not Obscured (Min) | Sticky case header, cookie banner | `scroll-padding-top` equal to header height; banner non-modal and dismissible | Playwright focus-visibility test |
> | 2.5.7 Dragging Movements | eBundle reorder | "Move up / Move down" buttons and position input alongside drag | Manual + unit test |
> | 3.3.7 Redundant Entry | Multi-step claim form | Party details carried forward; "Same as claimant address" option | Manual script |
> | 3.3.8 Accessible Authentication (Min) | Sign-in, step-up before award submission | Magic link / passkey; OTP field allows paste and autofill `one-time-code` | Manual |
> | 1.2.2 Captions (Prerecorded) | Hearing recordings | Captions from reviewed transcript | Media checklist |
> | 1.4.10 Reflow | All | No horizontal scroll at 320 CSS px except data tables with own scroll | Visual regression at 320 px |
> | 2.2.1 Timing Adjustable | Session timeout, payment hold | Warning at T-2 min, extend with one action | Playwright |

### `components` Component and pattern requirements (level 2)

List the shared design-system components this surface relies on and the accessibility contract each must honour (ARIA pattern, keyboard model, announcements, minimum target size). Page teams should inherit accessibility from components, not rebuild it.

Illustrative example (not a requirement):

> | Component (`packages/ui`) | APG pattern | Keyboard | Announcements |
> |---|---|---|---|
> | `DataTable` (case list) | Table (not grid) unless cells are editable | Tab to sortable headers, Enter sorts | Sort change via `aria-sort` + polite live region "Sorted by deadline, ascending" |
> | `DatePicker` (hearing date) | Dialog date picker | Arrow keys move day, PageUp/Down month, Esc closes | Selected date read with weekday and time zone |
> | `FileUpload` | Native `<input type=file>` + list | Remove buttons ≥ 24×24 px | Progress at 25% steps; scan result "Virus check passed" |
> | `Modal` | Dialog (modal) | Focus trapped, returns to trigger | Title as accessible name |
> | `Toast` | Status / alert | Not focus-stealing; persists ≥ 10 s or until dismissed | `role=status`, errors `role=alert` |

### `at` Assistive technology support matrix (level 1)

State which browser and assistive technology combinations are supported and tested, at what depth, based on who actually uses the platform (desktop counsel, mobile parties, secretariat staff on managed Windows machines). Keep it short enough to test every release.

Illustrative example (not a requirement):

> | AT | Browser / OS | Tier | Tested |
> |---|---|---|---|
> | NVDA (latest) | Chrome, Firefox / Windows 11 | 1 — full journey | Every release |
> | JAWS (latest) | Chrome / Windows 11 (secretariat machines) | 1 | Every release |
> | VoiceOver | Safari / iOS 18+ (parties on phones) | 1 | Every release |
> | TalkBack | Chrome / Android 14+ | 1 (large share of India parties on Android) | Every release |
> | VoiceOver | Safari / macOS | 2 — smoke test | Monthly |
> | Dragon / Voice Access | Windows / Android | 2 | Quarterly |
> | Windows Contrast Themes, 200% / 400% zoom | Edge, Chrome | 1 | Every release |
> 
> Indian-language screen reading (e.g. Hindi with NVDA eSpeak voices) checked once per new locale.

### `documents` Documents, media and generated output (level 2)

Cover everything the surface produces or displays that is not HTML: PDFs (receipts, procedural orders, awards, eBundles), uploaded third-party documents, hearing recordings, live hearings, transcripts and AI-generated text. Say what the platform guarantees for content it generates versus content users upload.

Illustrative example (not a requirement):

> | Output | Requirement | Owner |
> |---|---|---|
> | Filing receipt, procedural order, award (generated) | Tagged PDF conforming to PDF/UA (ISO 14289-1): reading order, headings, language set, table headers; HTML version offered alongside | Documents domain |
> | Uploaded pleadings (user content) | Not remediated; OCR text layer added so screen readers and search work; banner "This document was uploaded by a party and may not be accessible. Request an accessible copy." | Documents domain + secretariat |
> | eBundle | Bookmarks per tab, page labels matching index, OCR layer | Bundling pipeline |
> | Hearing recording | Captions from reviewed transcript within agreed turnaround; transcript downloadable | Transcribers domain |
> | Live hearing | Live captions or CART on request; sign-language interpreter tile pinned; chat meets real-time text clauses | Hearings domain |

### `tenant` Tenant theming and configuration guardrails (level 2)

Explain how tenant branding, custom fields, form-builder forms, tenant-written copy and tenant-uploaded templates are prevented from breaking conformance, and what the tenant admin sees when a choice would fail.

Illustrative example (not a requirement):

> - Theme tokens validated on save: text contrast ≥ 4.5:1, UI components and focus ring ≥ 3:1 against both light and dark surfaces. Failing palette is rejected with the failing pair shown ("Primary button text on #F2A900 is 2.1:1; needs 4.5:1").
> - HKIAC-style dark-navy theme and a SEBI ODR institution's saffron theme both pass after automatic text-colour selection.
> - Form builder: label required for every field; placeholder-only labels impossible; field types limited to accessible components.
> - Tenant logo requires alt text; tenant-supplied email templates linted for alt text, link text and heading order before activation.

### `testing` Testing method (level 1)

Describe how conformance is established and kept: automated rules in CI, manual expert review against every applicable criterion, AT testing per the matrix, and testing with disabled users. Name the sample of pages and states, following WCAG-EM.

Illustrative example (not a requirement):

> 1. **Automated (every PR):** axe-core via Playwright on all Storybook stories and on 31 journey states; build fails on any serious or critical violation.
> 2. **Manual expert review (each release touching the surface):** WCAG 2.2 AA checklist on the WCAG-EM sample (14 page templates + random sample of 5 real case pages in staging with synthetic data).
> 3. **AT passes:** scripted journeys per the AT matrix ("File a reply with two annexures before deadline").
> 4. **Users with disabilities:** twice a year, 5–8 participants incl. screen-reader, low-vision, motor and cognitive disabilities, recruited in India and Singapore.
> 5. **Third-party audit:** annual, by an IAAP-certified auditor (needed by SEBI MII tenants).
> 
> Automated tools find only part of the issues; a release is not "conformant" on automated results alone.

### `exceptions` Known exceptions and remediation plan (level 2)

List every known failure or partial support, its impact on users, the workaround offered, the owner and the fix date. Exceptions must be visible in the ACR and accessibility statement, not hidden.

Illustrative example (not a requirement):

> | ID | Criterion | Issue | User impact | Workaround | Owner | Fix by |
> |---|---|---|---|---|---|---|
> | AX-112 | 2.5.7 | Bundle reorder drag-only in legacy viewer | Motor-impaired counsel cannot reorder | Secretariat reorders on request within 1 working day | Bundling team | 15 Jan |
> | AX-118 | 1.2.4 Captions (Live) | Live captions only in English | Hindi-speaking deaf party | CART provider booked on request | Hearings | Vendor review Q1 |
> | AX-121 | 1.1.1 | Uploaded scanned exhibits have no alt text | Blind party cannot read images | OCR text + accessible copy on request | Policy (user content) | Not fixable by platform; documented |

### `reporting` Conformance reporting (level 2)

Specify the reports this surface feeds: the Accessibility Conformance Report (VPAT format editions for WCAG, Section 508, EN 301 549 / IS 17802), the public accessibility statement, and regulator or client audit evidence. Say who signs, how often and where it is published.

Illustrative example (not a requirement):

> - **ACR:** VPAT INT edition (current ITI version) (WCAG 2.2, Revised 508, EN 301 549) per product release; also a machine-readable JSON copy in case the draft RPwD amendment's format requirement is finalised.
> - **Signatory:** CTO; evaluator named with IAAP credential.
> - **Accessibility statement:** per tenant at `/accessibility`, generated from the ACR plus tenant contact for accommodation requests; dated, reviewed at least yearly.
> - **SEBI MII tenants:** evidence pack (auditor report, remediation tracker, platform list) delivered to the MII ahead of its annual audit deadline.

### `support` Feedback, accommodation and grievance (level 3)

How a person with a disability reports a barrier or asks for an accommodation (accessible copy, extension, interpreter, alternative channel), who responds, and in what time. Link the human-task workflow.

Illustrative example (not a requirement):

> - "Report an accessibility problem" link in the footer of every page and email; form is itself conformant and also offers email and phone.
> - Routed to the tenant's nodal officer and to Nomology support; acknowledgement within 1 working day, resolution or workaround within 5.
> - Accommodation requests that affect deadlines (for example extra time for a party using a screen reader with a 900-page bundle) are routed to the tribunal secretary as a procedural request, never decided by support staff.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Are ODR-institution tenants SEBI regulated entities in their own right, or only the MIIs?
> - [ ] Do we claim WCAG 2.2 AA in contracts now, or 2.1 AA with 2.2 as a goal?
> - [ ] Will we offer live captions in Hindi and other Indian languages, and through which vendor?

## Checks

### `applicability` Legal applicability and allocation

**Question:** For each tenant type and region this surface serves, who is legally responsible for accessibility, under which instrument, and are those duties reflected in our contracts and in the tenant's obligations to its regulator?

- Which tenants are government bodies (GIGW, ADA Title II), SEBI-regulated entities or MIIs (SEBI circular of 31 July 2025), or private institutions (RPwD Act s.46 service providers), and is that recorded per tenant in tenant settings?
- Does the master service agreement state the conformance target, who remediates, response times for accessibility defects, and who pays for third-party audits that a tenant's regulator requires?
- Under the draft RPwD amendment, an establishment cannot rely on a supplier's ACR without due diligence. What evidence do we give tenants so their verification is quick and credible?
- Which instruments are still draft or under litigation (draft RPwD amendment rules, EN 301 549 v4.1.1 harmonisation), who watches for final versions, and what is the trigger to update this node?
- Has counsel confirmed whether the European Accessibility Act or US ADA Title III exposure exists for any tenant, rather than assuming it does or does not?
- If a tenant demands a lower target than our platform standard (for example "WCAG 2.0 is enough"), can it opt out, and how is that prevented from reducing the platform for others?

**Good answer:** A per-tenant-type table naming the instrument, standard, obligated party and contract clause, signed off by legal, with draft instruments clearly marked and an owner watching them. Contracts state the target (WCAG 2.2 AA), remediation SLAs and audit cost allocation, and we hand tenants an evidence pack that satisfies their verification duty.

**Red flags:**

- "Accessibility law doesn't apply to private B2B software" asserted without legal review.
- No record of which tenants are SEBI-regulated or government bodies.
- Contracts silent on accessibility, or promising full conformance we cannot evidence.
- Draft rules treated as final, or final rules ignored.

### `evidence` Integrity of the conformance claim

**Question:** Would our conformance claim for this surface survive an independent audit or a complaint to the Chief Commissioner, and is every statement in the ACR backed by test evidence?

- Is the claim scoped to named pages, states and versions, and does it include the states auditors find most failures in (errors, empty states, timeouts, modals)?
- For each criterion marked "Supports", is there a stored test record (date, tester, method, AT used, build hash)?
- How are "Partially supports" items described so a reader understands the real impact, rather than vague wording?
- Is a third-party content exception (uploaded pleadings, tenant-supplied text) claimed, and is it the narrow, statement-based kind WCAG permits rather than a blanket excuse?
- Who reviews the ACR before signature, and is there a rule that the ACR is re-issued after major UI changes?
- Are AI-generated captions, alt text or summaries counted as conformant only after human review?

**Good answer:** A versioned ACR where every row links to test evidence in the repository or test-management tool, a named qualified evaluator, a signatory, and a rule that a major release cannot ship without a refreshed ACR. Partial support and exceptions are described in terms of user impact with workarounds.

**Red flags:**

- ACR filled in from automated scan results only.
- "Supports" claimed for criteria never manually tested.
- No version or date on the ACR, or one reused across products.
- Machine-generated captions or alt text counted as conformant without review.

### `tenancy` Tenant customisation and content

**Question:** Can any tenant configuration, branding, form, template or tenant-written content break conformance for that tenant's users, and what stops it?

- Which tenant-configurable elements can affect accessibility: colours, fonts, logos, custom fields, form-builder forms, email and document templates, landing-page rich text, embedded third-party scripts?
- Is each one validated at save time (contrast, labels, alt text, heading order), and what does the tenant admin see when it fails?
- Can a tenant inject custom CSS or scripts? If so, how are focus styles, motion preferences and screen-reader behaviour protected?
- Is a theme checked in both light and dark modes, high-contrast mode and at 400% zoom before activation?
- Who owns remediation if a tenant's own uploaded document templates (for example an institution's award template) produce untagged PDFs?
- Does each tenant's accessibility statement reflect that tenant's configuration and contacts, not a generic platform statement?

**Good answer:** An inventory of tenant-configurable elements with the automated check applied to each and blocked activation on failure, no arbitrary CSS or script injection, and a per-tenant statement generated from the platform ACR plus tenant-specific exceptions. Ownership of tenant-supplied templates is set out in the contract.

**Red flags:**

- Tenant themes activated without contrast checks.
- Form builder allows placeholder-only labels or inaccessible custom widgets.
- Arbitrary tenant CSS or JavaScript allowed.
- One generic accessibility statement for all tenants.

### `regression` Preventing regression

**Question:** Once conformant, what stops this surface from falling out of conformance through ordinary releases, dependency upgrades or new features?

- Which automated checks run on every pull request (axe on Storybook stories and journey states, lint rules such as jsx-a11y), and which severities fail the build?
- Are accessibility acceptance criteria part of the Definition of Done for every UI ticket, and who checks them in review?
- Is there a keyboard and focus-order end-to-end test for each critical journey (file, pay, accept appointment, submit award) in Playwright?
- How are design-system component changes tested for downstream accessibility impact before release?
- What is the defect SLA by severity (for example blocker: hotfix within 5 working days), and is it tracked on a dashboard?
- How often is a full manual audit repeated, and what triggers an unscheduled one (new persona, major redesign, new AT version)?

**Good answer:** Build-blocking automated checks on components and journey states, keyboard end-to-end tests for each critical journey, accessibility criteria in the Definition of Done, severity-based defect SLAs with tracking, and a scheduled manual audit cycle with defined triggers.

**Red flags:**

- Accessibility tested once before launch and never again.
- Automated violations reported but never block the build.
- No severity scheme or SLA for accessibility defects.
- Component library changes shipped without accessibility review.

### `identity` Authentication and identity verification

**Question:** Can a person with any disability sign in, pass step-up checks and complete identity or KYC verification on this surface without help from another person?

- Does every authentication path meet 3.3.8 Accessible Authentication: paste and password-manager support, no puzzle CAPTCHAs, passkey or magic-link options?
- Do OTPs by SMS or email allow enough time and a resend, and is the time limit adjustable or long enough (2.2.1)?
- Where video KYC or liveness checks are used, what alternative exists for blind users, users with facial differences or acid-attack survivors, as directed by the Supreme Court in Pragya Prasun v. Union of India (30 April 2025)?
- Is any bot protection (for example a CAPTCHA provider) accessible, and what is the fallback when it fails?
- Can a lawful guardian or authorised representative act for a person with a disability, as DPDP Act s.9 contemplates for consent, and is that relationship shown in the UI and audit trail?
- Is step-up before consequential actions (submitting an award, changing bank details) accessible by the same standards?

**Good answer:** Every sign-in, step-up and KYC path is listed with its accessible method and a human-assisted fallback that does not make the user disclose more than needed. Liveness and video KYC have a documented alternative, guardian or representative flows exist, and these paths are in the AT test scripts.

**Red flags:**

- Image or audio CAPTCHA as the only bot check.
- Liveness check with no alternative path.
- OTP expires in under a minute with no extension.
- Assisted sign-in that requires sharing credentials with a helper.

### `due-process` Equal participation in proceedings

**Question:** Can a party, counsel or neutral with a disability take part in the proceedings on equal terms, including meeting deadlines, reading the record and attending hearings?

- Can a user request an accommodation (accessible copy of a bundle, extra time, interpreter, CART) from within the case, and is the request routed to the tribunal secretary as a procedural request with a timer?
- Are deadlines and time limits shown in ways that work with screen readers and cognitive disabilities (absolute date, time zone, plain countdown) and are reminders sent through the user's chosen accessible channel?
- When an opposing party uploads an inaccessible document, how quickly can an accessible version be obtained and does the deadline account for the delay?
- Do hearings support sign-language interpreter pinning, live captions in the hearing language, and keyboard control of the hearing room?
- Are transcripts and recordings delivered in accessible formats within the same turnaround as for other users?
- Is a record kept of accommodations granted, visible to the tribunal but protected as sensitive personal data?

**Good answer:** A defined accommodation workflow with timers and tribunal decision, accessible deadline display and reminders, a turnaround target for accessible copies of uploaded documents, and hearing features for interpreters and captions. Disability information is stored as sensitive data with restricted access.

**Red flags:**

- Accommodation handled informally by email with no record.
- Deadlines that run while a party waits for an accessible copy.
- Hearing room with no caption or interpreter support.
- Disability details visible to opposing parties.

### `third-party` Third-party and embedded components

**Question:** Which third-party services appear inside this surface (video conferencing, e-signature, payment gateways, document viewers, chat or help widgets, KYC providers), and how is their accessibility assured?

- Is there a list of every embedded or redirected third-party component with its current ACR or VPAT and its date?
- Has each been tested in our journey with our AT matrix, not only accepted on the vendor's word?
- Is accessibility a procurement criterion and a contract term (conformance target, remediation SLA) for new vendors?
- What is the fallback when a vendor component is inaccessible (for example a payment page that fails with screen readers): an alternative payment route, assisted payment, offline option?
- Do third-party widgets obscure focus or trap keyboard users (2.4.11, 2.1.2)?
- How are vendor regressions detected after their releases?

**Good answer:** A register of third-party components with dated ACRs and our own test results, accessibility in procurement and contract terms, a working alternative route for each critical vendor step, and periodic re-testing after vendor releases.

**Red flags:**

- Vendor ACR accepted without our own testing.
- No alternative when a payment or e-signature step is inaccessible.
- Chat or cookie widgets that trap focus or hide focused content.
- No accessibility terms in vendor contracts.

### `feedback` People with disabilities in the loop

**Question:** How do people with disabilities shape and check this surface, and how are their complaints handled and learned from?

- When were people with disabilities last involved in research or testing for this surface, which disabilities were represented, and what changed as a result?
- Is the feedback and grievance channel itself accessible, offered in more than one form, and staffed with a named nodal officer for regulated tenants?
- What are the acknowledgement and resolution targets, and are they met (tracked monthly)?
- Are complaints classified by criterion and fed into the exceptions register and backlog?
- Are support and secretariat staff trained to assist users with disabilities, as SEBI's guidelines and the Pragya Prasun directions expect?
- Are participants paid and is their personal data handled under the research consent process?

**Good answer:** A cadence of research and testing with disabled participants with outcomes recorded, an accessible multi-channel grievance route with named owners and measured targets, complaints feeding the backlog, and trained support staff.

**Red flags:**

- No testing with disabled users at all.
- Grievance route only through an inaccessible form.
- Complaints closed without a fix or workaround.
- Support staff with no accessibility training.

