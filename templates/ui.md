# Template: UI screen and user journey (`ui`)

Generated from `ui.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies what a person sees and does to complete a task, screen by screen, including every state, so design and engineering build the same thing.

**Depth:** 2–6 pages per journey. Every screen lists its states (loading, empty, error, partial, success). Link to design files instead of embedding pixel detail. Accessibility criteria are mandatory for Approved.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `persona` Persona and goal (level 1)

Who, in what situation, wants to achieve what. One journey = one goal.

Illustrative example (not a requirement):

> Respondent's counsel, invited to an SEBI ODR case by email, wants to file a reply before the deadline without phoning the institution.

### `journey` Journey steps (level 1)

The steps from entry to goal, including where the user comes from and where they end up.

Illustrative example (not a requirement):

> 1. Opens invitation email → lands on sign-in (magic link)
> 2. Accepts representation → case overview
> 3. Sees "Reply due in 6 days" → opens filing form
> 4. Uploads reply and annexures → reviews → submits
> 5. Receipt screen with filing reference; email confirmation

### `screens` Screens (level 1)

Each screen: purpose, key content, primary and secondary actions, link to design.

Illustrative example (not a requirement):

> | Screen | Shows | Primary action |
> |---|---|---|
> | Case overview | Stage, next deadline, parties, recent filings | File a document |
> | Filing form | Document type, files, description, declaration | Submit filing |
> | Receipt | Filing reference, served-on list, timestamp | Back to case |

### `states` States per screen (level 1)

Loading, empty, error, partial, permission-denied and success states with their copy.

Illustrative example (not a requirement):

> **Filing form**
> - Upload failed: "This file didn't upload. Check it's under 50 MB and try again."
> - Deadline passed: form disabled, message "The reply deadline passed on 14 Nov. Ask the secretariat for an extension."
> - Virus scan pending: submit disabled with "Checking your files…"

### `validation` Validation and business rules (level 2)

Field validation and rule-driven behaviour, referencing Decision nodes.

Illustrative example (not a requirement):

> - File types: PDF, DOCX, JPG; max 50 MB each, 200 MB per filing
> - Declaration checkbox required
> - Deadline from case Deadlines; extension rules per Decision "Filing extensions"

### `content` Content and copy (level 2)

Key labels, help text, legal text, and tone; who approves legal copy.

Illustrative example (not a requirement):

> Declaration text supplied by tenant (configurable); default: "I confirm this filing is made on behalf of the party I represent."

### `accessibility` Accessibility (level 2)

Specific WCAG 2.2 AA criteria that need attention on these screens.

Illustrative example (not a requirement):

> - Upload control operable by keyboard; progress announced to screen readers
> - Errors identified in text, not colour alone (1.4.1, 3.3.1)
> - Target size ≥ 24×24 px for remove-file buttons (2.5.8)

### `responsive` Devices and responsiveness (level 2)

Supported devices and what changes on small screens.

Illustrative example (not a requirement):

> Fully usable on phone: counsel often check deadlines on mobile. Multi-file upload falls back to one-at-a-time on iOS Safari if needed.

### `analytics` Analytics events (level 3)

Events to track for usage analytics.

Illustrative example (not a requirement):

> `filing.started`, `filing.submitted`, `filing.abandoned` (with step), all with tenantId and caseType.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Do we allow saving a filing as draft?

## Checks

### `tenancy` Tenancy and branding

**Question:** How do these screens resolve and display the right tenant (branding, labels, fields, legal text), and what guarantees that a user never sees another tenant's data, branding or cached content?

- How is the tenant determined for this journey (subdomain, custom domain, path), and what does a user who belongs to several tenants (for example counsel at two institutions) see? Is the active tenant always visible on screen?
- Which elements are tenant-configurable: logo, colours, product name, terminology (award vs decision), extra fields, legal notices, support contacts? Where is each configured (tenant settings or a Decision node)?
- Do tenant colour themes still meet WCAG contrast (4.5:1 for text, 3:1 for UI components and focus indicators)? Who checks a tenant theme before it goes live?
- Are tenant-specific fields rendered from a schema with validation, labels and help text per tenant, rather than custom code per tenant?
- Can pages or API responses be cached by the CDN, Next.js data cache or browser in a way that serves one tenant's content to another? Are cache keys tenant-scoped and are authenticated pages marked private?
- Are emails, PDFs and downloads generated from this journey branded and labelled for the same tenant?

**Good answer:** A list of tenant-configurable elements with their configuration source and defaults, a rule that tenant themes are validated against WCAG contrast before activation, and a stated caching rule (tenant in every cache key, authenticated responses not shared). Multi-tenant users switch tenant explicitly and the active tenant is always shown.

**Red flags:**

- Tenant-specific screens built by copying components per tenant.
- Shared caching of authenticated pages or data without the tenant in the key.
- Tenant brand colours applied without contrast checks.
- No indication of which tenant a multi-tenant user is acting in.

### `security` Access and data exposure

**Question:** Does every screen, action and data request in this journey enforce the permission matrix on the server, and does the page send the browser only the data this user is allowed to see?

- For each screen and action, which permission and case relationship is required (link the Security node), and what does a user without it see: hidden, disabled with a reason, or a permission-denied state?
- Are server actions, route handlers and React Server Components checking permissions on the server for every request, not relying on the UI hiding a button?
- Do server components or API responses serialise more fields than the screen shows (for example a neutral's fee rate or a sealed document title in the page payload)? How is the response shaped per role?
- Are record IDs in URLs safe against guessing (another case ID in the URL returns not-found, not a different tenant's case)?
- How are uploads handled: file type and size limits, malware scanning before anyone can open them, and preview without running active content?
- What happens when a session expires or a role is revoked mid-journey (for example a neutral recused while the screen is open)? Does the next request fail safely and does the user keep unsaved work?
- Are sensitive actions (accepting appointment, submitting an award, changing payout bank details) protected by re-authentication or step-up, and by CSRF protection?

**Good answer:** A screen-by-action table with required permission, server enforcement point and denied state, plus a statement that responses are shaped per role with no hidden fields in payloads. The answer covers ID-guessing behaviour, upload scanning, session expiry and step-up for sensitive actions, and names the authorisation tests that cover these screens.

**Red flags:**

- "The button is hidden for other roles" as the only control.
- Page payloads that include fields the role cannot see.
- Direct object references that reveal whether another tenant's record exists.
- Uploaded files available to others before malware scanning.

### `accessibility` Accessibility (WCAG 2.2 AA)

**Question:** Can every step of this journey be completed by keyboard, screen reader, voice control, screen magnification and by people with cognitive impairments, meeting WCAG 2.2 AA, and how is that verified?

- Is the full journey operable by keyboard alone, with a logical focus order, a visible focus indicator, and no focused element hidden behind sticky headers, cookie banners or chat widgets (2.4.11 Focus Not Obscured)?
- Which complex widgets appear (data tables of cases, date pickers, document viewers, drag-and-drop bundle ordering, multi-step forms, modals), and which ARIA Authoring Practices pattern does each follow? Does every drag action have a single-pointer alternative (2.5.7 Dragging Movements)?
- Are all form fields labelled, are errors identified in text and linked to the field, and are suggestions given (3.3.1, 3.3.3)? Is information already entered not asked for again in the same process (3.3.7 Redundant Entry)?
- Does sign-in or step-up avoid cognitive function tests, or offer an alternative such as paste-friendly fields, passkeys or a magic link (3.3.8 Accessible Authentication)?
- Are target sizes at least 24 by 24 CSS pixels or adequately spaced (2.5.8), and is help offered in a consistent place on every screen (3.2.6 Consistent Help)?
- Do status changes (saved, uploaded, filing submitted, deadline approaching) get announced to screen readers through live regions without moving focus?
- Are uploaded or generated documents (procedural orders, awards, transcripts) accessible: tagged PDFs, reading order, text not images? Are hearing recordings captioned and transcripts provided?
- How is it tested: automated checks in CI (for example axe), manual keyboard and screen-reader passes (NVDA with Firefox or Chrome, VoiceOver with Safari), and testing with disabled users before Approved?

**Good answer:** A list of the WCAG 2.2 AA success criteria that need special attention on these screens with how each is met, the ARIA pattern used for every complex widget, and a test plan combining automated CI checks with manual keyboard and screen-reader passes on named browser and assistive-technology pairs. Generated documents and media in the journey have their own accessibility requirement.

**Red flags:**

- "We will run Lighthouse" as the only accessibility test.
- Custom widgets with no keyboard support or ARIA pattern.
- Drag-and-drop with no single-pointer alternative.
- Errors shown only by colour or only at the top of the form without field association.

### `i18n` Localisation

**Question:** Can this journey be translated, formatted and laid out for every language, script, time zone and currency its tenants need, without code changes?

- Is every user-facing string, including errors, empty states, emails and PDF text, externalised with an ID and translator notes? Are plurals and gendered forms handled with ICU message format rather than string concatenation?
- Which locales are needed at launch (for example English, Hindi and other Indian languages, Simplified and Traditional Chinese for HKIAC) and which are planned? Is the language switch remembered per user?
- Are dates, times, numbers and currency formatted from CLDR data through the platform's formatting helpers (Intl API), never by hand?
- Is the time zone of every displayed deadline explicit (for example "17:00 HKT, seat time" alongside the user's local time), with no ambiguity about which applies?
- Does the layout work with right-to-left scripts (CSS logical properties, mirrored icons where meaningful, dir attribute) and with text that expands by 30–40% in translation?
- Can user-entered names, addresses and identifiers use non-Latin scripts, and do inputs avoid forcing a first name / last name split?
- Who reviews translations of legal copy, and how is the authoritative language of a legal notice indicated?

**Good answer:** All strings externalised with ICU messages, a named list of launch locales, formatting through Intl / CLDR-backed helpers, explicit time-zone labelling for deadlines, layouts using logical properties and tested with a pseudo-locale for expansion and RTL. Translations of legal text are reviewed by a named qualified person and the authoritative language is stated.

**Red flags:**

- Hard-coded strings or concatenated sentences.
- Deadlines shown without a time zone.
- Layouts using left / right physical properties that break in RTL.
- Machine-translated legal copy with no review.

### `consequential` Consequential actions

**Question:** For every action in this journey that has legal or financial effect, does the user clearly understand what will happen, confirm it, and receive durable proof of what they did and when?

- List the actions with legal or financial effect (for example file a claim, serve a notice, accept appointment and sign a declaration of independence, submit an award, pay a fee, withdraw a case). Which are irreversible?
- Before submission, does the user see a review step showing exactly what will be submitted, to whom, and the consequence, with a clear way to go back and correct it (3.3.4 Error Prevention)?
- Is the deadline that the action relates to shown with time remaining and time zone, and what does the user see if they act just after it passes?
- After submission, what proof does the user receive: an on-screen receipt with reference number and server timestamp, an email, a downloadable copy?
- How is a double submission prevented (double click, back button, network retry) and what does the user see if it happens?
- Where electronic signature or a declaration is needed, which method and wording are used, and who in legal approved them?
- For actions taken on behalf of someone else (counsel for a party, secretariat for a neutral), is the on-behalf-of relationship shown before confirmation and in the receipt?

**Good answer:** A table of consequential actions with confirmation pattern, reversibility, proof provided and the legal approver of the wording. Every such action has a review step, a server-timestamped receipt with a reference number, idempotent submission, and a defined behaviour at the deadline boundary.

**Red flags:**

- Irreversible legal actions submitted with one click and no review step.
- Receipts using the browser's clock rather than the server timestamp.
- No protection against double submission.
- Declaration or signature wording not approved by legal.

### `resilience` Errors and resilience

**Question:** What does the user experience when things go wrong (slow network, server error, concurrent edit, session timeout, partial upload), and do they keep their work?

- For each screen, is there defined copy and a recovery action for loading, empty, error, partial and permission-denied states (link to the States section rather than repeating it)? Do errors say what happened and what to do next, without exposing internals?
- Are long forms (statement of claim, award drafting) saved as drafts automatically, and where is the draft stored (server, so it survives device change)? Is draft content protected like submitted content?
- If two people edit the same item (for example two secretariat users, or co-counsel), how is the conflict detected and shown? Does the second save get a clear message and a way to merge or reload?
- How are large uploads (multi-gigabyte hearing bundles, audio recordings) handled: resumable upload, progress, retry after network loss, and a clear state if processing (virus scan, OCR, transcription) is still running?
- When a session is about to time out, is the user warned and given at least 20 seconds to extend it (2.2.1 Timing Adjustable), and is unsaved work kept if it does expire?
- Does the journey still work on a poor connection typical of some parties (for example 3G mobile), and what is the behaviour when offline?

**Good answer:** Each screen has defined error and recovery behaviour, autosave for long forms with server-side drafts, optimistic-concurrency conflict handling with a clear message, resumable uploads with visible processing states, and an accessible session-timeout warning. The answer names the network profile used for testing.

**Red flags:**

- Generic "Something went wrong" with no next step.
- Long legal forms that lose content on session expiry or navigation.
- Last write wins silently on shared records.
- Large uploads that must restart from zero after a network drop.

### `performance` Performance

**Question:** What speed targets does this journey commit to on realistic devices and networks, for realistic data sizes, and how are they measured in production?

- What are the targets for Core Web Vitals at the 75th percentile (Largest Contentful Paint under 2.5 s, Interaction to Next Paint under 200 ms, Cumulative Layout Shift under 0.1), and on which device and network profile?
- What is the largest realistic data set on these screens (for example a case with 5,000 documents, a secretariat queue of 20,000 cases, a 6-hour transcript)? Are lists paginated or virtualised and searched on the server?
- Which data is rendered on the server, streamed, or loaded on interaction? What is the JavaScript bundle budget for the entry route?
- How are slow back-end operations (bundle generation, search across documents, AI summaries) presented: progress, background job with notification, or cancellable request?
- Is real-user monitoring in place per tenant and region, so a slow region (for example US users reaching the Singapore region) is visible?
- Is there a performance test with production-like data volumes before Approved?

**Good answer:** Numeric targets for Core Web Vitals at p75 on a stated device and network profile, a stated worst-case data size per screen with the pagination or virtualisation approach, a bundle budget enforced in CI, and real-user monitoring segmented by tenant and region. Long operations run as background jobs with visible progress.

**Red flags:**

- No numeric targets, or targets measured only on developer laptops.
- Client-side loading of full lists of cases or documents.
- No real-user monitoring.
- Blocking spinners for operations that can take minutes.

### `observability` Analytics and privacy

**Question:** Which interactions are tracked to judge whether this journey works, and is that tracking minimal, consented where required, free of case content and kept within the tenant's region?

- Which questions will analytics answer (for example where do parties abandon the filing journey, how long does a neutral take to accept appointment)? List each event with its properties.
- Do event properties exclude personal data and case content (no names, emails, case titles, document names, free text)? Are IDs pseudonymised?
- Is consent needed for this tracking under GDPR, the ePrivacy rules, DPDP or PDPA for each tenant's users, and how is it collected and honoured? Is non-essential tracking off until consent is given?
- Which analytics tool is used, where is the data stored, and does it respect the tenant's residency region? Is the vendor a listed sub-processor?
- Can a tenant switch analytics off or receive its own usage reports, and is this stated in the tenant contract?
- How long are analytics events kept, and are they deleted when a tenant is offboarded or a user's data is erased?
- Are front-end errors captured (with stack traces scrubbed of personal data) and linked to back-end traces?

**Good answer:** A short event list tied to named product questions, with properties that exclude personal data and case content, a stated consent approach per region, an analytics store located in the tenant's region and listed as a sub-processor, a retention period and tenant opt-out. Front-end errors are captured with personal data scrubbed.

**Red flags:**

- Session replay or autocapture of all inputs on screens with case content.
- Personal data or case titles in event properties.
- Analytics sent to a vendor region different from the tenant's residency region with no transfer basis.
- Tracking events with no stated question or owner.

