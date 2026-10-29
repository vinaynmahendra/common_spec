# Template: Content design and UX writing (`content`)

Generated from `content.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies the words users see — voice, terminology, microcopy, error messages, legal and declaration text, notifications and translations — and who owns each, so content is consistent, legally accurate and understandable by parties with and without lawyers.

**Depth:** 2–6 pages. Terminology, error and legal-text tables must be complete for the scope; examples must show final copy, not placeholders. Legal text owners and approvers are named. Split into children when one area (for example notifications or errors) exceeds about 40 strings or has its own approval process.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `scope` Scope and audiences (level 1)

Say which surfaces and channels this content node governs (screens, emails, SMS, WhatsApp, PDFs, API error text, help articles) and who reads them, including their legal knowledge, language and likely stress level.

Illustrative example (not a requirement):

> **Covers:** all copy in the party / counsel filing journey, its notifications and its receipt PDF.
> 
> | Audience | Legal knowledge | Typical context | Reading target |
> |---|---|---|---|
> | Unrepresented retail investor (SEBI ODR) | None | Phone, first dispute, worried about money | Plain English / Hindi, short sentences; no Latin |
> | MSME owner claiming delayed payment | Low | Desktop or phone, time-poor | Plain language, numbers first |
> | Counsel in an HKIAC arbitration | Expert | Desktop, deadline-driven | Precise procedural terms allowed, still concise |
> | Tribunal secretary | Expert, process-heavy | All day in the console | Short labels, consistent verbs |

### `voice` Voice and tone (level 1)

Define the platform voice in a few principles and how tone shifts by situation. The platform is a neutral forum: copy must never appear to favour a party, predict an outcome or give legal advice.

Illustrative example (not a requirement):

> **Voice:** neutral, plain, respectful, precise.
> 
> | Situation | Tone | Example |
> |---|---|---|
> | Routine action | Direct | "Upload your reply." |
> | Deadline approaching | Calm, specific | "Your reply is due on 14 Nov 2026 at 17:00 IST (3 days left)." |
> | Adverse outcome (claim dismissed, award against party) | Factual, no judgement | "The tribunal has issued its award. Read the award." — never "Unfortunately, you lost." |
> | System failure | Accountable | "We couldn't save your filing. Nothing was submitted. Try again." |
> 
> Never: "You should file a counter-claim" (advice), "Great news!" on decisions, humour, exclamation marks in case communications.

### `terminology` Terminology and glossary alignment (level 1)

List the canonical terms this content uses, tied to the domain model's ubiquitous language, the permitted tenant or procedure-type variants, and banned synonyms. One concept, one term, everywhere: UI, emails, PDFs, API and help centre.

Illustrative example (not a requirement):

> | Concept (domain ID) | Canonical term | Tenant / procedure variants | Do not use | Plain explanation shown on first use |
> |---|---|---|---|---|
> | `Case` | case | "matter" (HKIAC), "dispute" (SEBI ODR) | file, ticket | — |
> | `Award` | award | "settlement agreement" (conciliation), "decision" (adjudication) | judgment, verdict | "The tribunal's final decision, which is binding." |
> | `Neutral` | arbitrator / conciliator / mediator by role | — | judge, officer | — |
> | `Filing` | filing | "submission" (HKIAC) | upload, post | — |
> | `Claimant` | claimant | "applicant" where tenant rules say so | complainant | "The party that started the case." |
> 
> Variants come from tenant settings keyed to the domain ID, never from free text.

### `patterns` Microcopy patterns (level 1)

Specify the reusable patterns: button and link labels, field labels and hints, empty states, confirmations, success messages, status labels and time and date display. Give the rule and a good and bad example for each.

Illustrative example (not a requirement):

> | Pattern | Rule | Good | Bad |
> |---|---|---|---|
> | Primary button | Verb + object; names the consequence | "Submit reply" | "OK", "Proceed" |
> | Destructive confirm | Says what is lost and whether it can be undone | "Withdraw claim? The tribunal will be told and this cannot be undone." [Withdraw claim] [Keep claim] | "Are you sure?" [Yes] [No] |
> | Field hint | Before the field, not placeholder | "PDF or Word, up to 50 MB" | Placeholder "Upload here" |
> | Empty state | What it is, why empty, what next | "No filings yet. Filings from all parties appear here." | "No data" |
> | Date / deadline | Absolute date, time, zone; relative in brackets | "17:00 HKT, 14 Nov 2026 (in 3 days)" | "Due Friday" |
> | Status | Same label in list, detail and email | "Awaiting payment" | "Pending" in one place, "Unpaid" in another |

### `errors` Error messages (level 1)

Define the structure every error follows (what happened, why if useful, what to do now), where it appears, and the catalogue of errors for this scope with their codes. Errors must not blame, expose internals or reveal other parties' data.

Illustrative example (not a requirement):

> **Structure:** what happened → what to do. Shown next to the field and in a summary at top of the form, linked to the field (WCAG 3.3.1, 3.3.3).
> 
> | Code | Trigger | Message |
> |---|---|---|
> | `FILING_TOO_LARGE` | File > 50 MB | "'Annex 4.pdf' is 63 MB. Files must be 50 MB or smaller. Split the file or compress it." |
> | `DEADLINE_PASSED` | Submit after deadline | "The deadline for replies passed at 17:00 IST on 14 Nov. Your reply was not submitted. You can ask the secretariat for an extension." [Request extension] |
> | `SCAN_FAILED` | Virus found | "We couldn't accept 'Exhibit C.docx' because it may contain harmful code. Upload a different copy." |
> | `NOT_FOUND` | Case ID not visible to user | "We can't find that case, or you don't have access to it." (same text whether it exists or not) |
> | `INTERNAL` | Unexpected | "Something went wrong on our side and your filing was not submitted. Try again in a few minutes. Reference: 7F3K-92QA." |

### `legal` Legal and declaration text (level 1)

List every piece of text with legal effect (declarations, consents, privacy notices, terms, service and receipt wording, signature statements), who owns and approves it (Nomology legal, the tenant, or the rules of the institution), how it is versioned, and how the version a user saw is recorded.

Illustrative example (not a requirement):

> | Text | Owner | Approver | Configurable by tenant | Versioned / recorded |
> |---|---|---|---|---|
> | Filing declaration | Tenant (institution rules) | Tenant counsel | Yes, with platform default | Version ID stored on each filing |
> | Arbitrator declaration of independence | Tenant | Tenant counsel | Yes | Signed copy stored with appointment |
> | Platform terms of use | Nomology (NTPL / TAPL / US entity by region) | Nomology legal | No | Acceptance logged per user |
> | Privacy notice (DPDP s.5 itemised notice, GDPR Art. 13) | Data fiduciary — usually the tenant; Nomology for platform accounts | Respective DPO / legal | Partly | Version shown at consent logged |
> | Electronic service wording on receipts | Tenant | Tenant counsel | Yes | Embedded in receipt PDF |
> 
> Plain-language summaries may sit beside legal text but never replace it, and say "This summary is for information. The full text applies."

### `notifications` Notifications and generated documents (level 2)

Specify copy for email, SMS, WhatsApp, in-app and push notifications and for generated PDFs: subject lines, length limits, what case detail may appear outside the platform, and channel-specific approval steps.

Illustrative example (not a requirement):

> - **Email subject:** "[HKIAC] New filing in case ARB-2026-0412" — case reference only, never party names or claim value.
> - **SMS (India):** template text must be pre-registered with the sender's telecom DLT platform under TRAI rules before use, so wording changes need lead time. Example: "CORD: A new document was filed in your case {#var#}. Sign in to view: {#var#}".
> - **WhatsApp:** template submitted for approval; one call to action; no attachments with case content.
> - **Lock-screen safe:** push and SMS never say "claim against you" or the amount.
> - **Generated PDFs:** headings and labels come from the same string catalogue as the UI.

### `plain` Plain language for non-lawyer parties (level 2)

Set the plain-language rules for screens used by parties without lawyers: reading level, sentence length, how legal terms are introduced, use of examples, and what must stay precise. Explain procedural meaning without giving legal advice.

Illustrative example (not a requirement):

> - Sentences average under 20 words; one idea per sentence; active voice.
> - Legal terms kept where the law uses them, explained once inline: "**Statement of claim** — your written explanation of what happened and what you are asking for."
> - Banned without explanation: *inter alia, prima facie, sine die, without prejudice, ex parte*.
> - Each step answers "what is this, what do I do, what happens next, by when".
> - Example for SEBI ODR: "If you and the broker do not agree in conciliation, you can ask for arbitration. You will have 7 days to decide." (period illustrative; comes from the rules engine).
> - Tested with 5+ non-lawyer participants per major journey; target task success ≥ 90% without help.

### `localisation` Localisation readiness (level 2)

Make the content translatable without rewriting: externalised strings with stable IDs, ICU message syntax for plurals and variables, translator notes, length allowances, locale-aware formatting and a rule for which language version is authoritative.

Illustrative example (not a requirement):

> ```json
> "filing.deadline.remaining": {
>   "message": "{days, plural, =0 {Due today} one {# day left} other {# days left}}",
>   "note": "Shown next to an absolute deadline. 'days' is whole days in the seat's time zone. Max 24 chars in English; allow 40%."
> }
> ```
> - No concatenation ("You have " + n + " days").
> - Dates, numbers and currency via Intl / CLDR helpers (₹1,25,000 in en-IN; HK$125,000 in en-HK).
> - Launch locales per tenant (e.g. en-IN, hi-IN; en-HK, zh-Hant-HK). DPDP s.5(3) lets the data principal access the notice in English or any Eighth Schedule language — plan notice translations accordingly.
> - Legal text: translation by a qualified legal translator; the authoritative language is stated on the page ("The English version applies if versions differ").

### `accessibility` Accessible content (level 2)

Rules that make the words themselves accessible: headings, link and button text that makes sense out of context, alternative text, labels and instructions that do not rely on sensory characteristics, and language marking.

Illustrative example (not a requirement):

> - Link text names the destination: "Read procedural order no. 3" not "Click here" (2.4.4).
> - Instructions do not depend on shape or position: "Select Submit reply" not "Press the green button on the right" (1.3.3).
> - Page `lang` set per locale; inline foreign phrases marked with `lang` (3.1.2), e.g. a Chinese party name in an English page.
> - Alt text for tenant logos is the institution name; decorative icons have empty alt.
> - Accessible names of icon buttons come from the string catalogue ("Remove file Annex 4.pdf").

### `governance` Content governance and workflow (level 2)

Who writes, reviews and approves copy; where strings live; how tenant overrides are made, previewed and audited; and how copy changes ship (with code, or as content without a deploy).

Illustrative example (not a requirement):

> | Content type | Source of truth | Writer | Reviewer | Ships via |
> |---|---|---|---|---|
> | UI strings | `packages/i18n/messages/en.json` | Content designer | Product + engineer in PR | Code release |
> | Tenant terminology overrides | Tenant settings, keyed by domain term ID | Tenant admin | Preview + audit log | Immediate, versioned |
> | Legal / declaration text | Legal text register | Legal | Legal + tenant counsel | Content release with version ID |
> | Notification templates | Notification template store | Content designer | Ops for DLT / WhatsApp approval | Template activation |
> 
> CODEOWNERS makes the content designer a required reviewer on message-catalogue changes.

### `inventory` String inventory (level 3)

Optional: a table of the key strings in scope with IDs, final copy and status, so reviewers can read the content in one place.

Illustrative example (not a requirement):

> | ID | Copy (en) | Status |
> |---|---|---|
> | `filing.submit.button` | Submit reply | Approved |
> | `filing.review.heading` | Check your reply before you submit | Approved |
> | `filing.receipt.heading` | Reply submitted | Draft |
> | `filing.receipt.body` | We sent a copy to all parties and the tribunal at {time}. Your reference is {ref}. | In legal review |

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Can tenants override error messages, or only terminology?
> - [ ] Which Indian languages are needed for SEBI ODR parties at launch?
> - [ ] Who approves Hindi translations of the filing declaration?

## Checks

### `legal-accuracy` Legal meaning and approval

**Question:** Does every piece of copy that describes a legal step, right, deadline or consequence say exactly what the governing rules say, and has the right person approved it?

- Which strings describe legal effect (service, deemed receipt, deadlines, finality of an award, withdrawal, waiver), and is each traced to a rule, a tenant's institutional rules or a statute?
- When copy is simplified for non-lawyers, who checks that the simplification has not changed the legal meaning?
- Does any copy predict outcomes, recommend actions or explain options in a way that could be read as legal advice or as favouring one party?
- Where institutional rules differ (HKIAC vs a SEBI ODR institution), is the wording driven from tenant configuration rather than one hard-coded version?
- Are numbers in copy (days, fees, limits) inserted from the rules engine or settings rather than typed into strings, so a rule change cannot leave stale text?
- Who is the named approver for each class of legal text, and what is the turnaround for urgent fixes?

**Good answer:** A register of legally significant strings, each linked to its source rule and a named approver, with values injected from configuration rather than hard-coded. Plain-language versions are reviewed by a lawyer for equivalence, and copy never advises or predicts.

**Red flags:**

- Deadline periods or fees typed into copy.
- Simplified legal text published without legal review.
- Copy that recommends a course of action to a party.
- One set of procedural wording used for all institutions.

### `terminology` Terminology consistency

**Question:** Is every concept in this scope named with one canonical term, used identically across UI, notifications, documents, API messages and help, with tenant variants applied consistently?

- Is each term in this scope present in the platform glossary and tied to a domain model ID?
- When a tenant renames a concept ("matter" for "case"), does the change reach emails, PDFs, search labels, exports and help articles, not only the screen?
- Are banned synonyms checked automatically (lint on the message catalogue, glossary checks in the translation tool)?
- Do translations use the approved glossary term in each language, held in translation memory?
- Are API error messages and webhook field descriptions using the same terms as the UI, or do developers see different words?
- How is a new term added, and who resolves disputes between product, legal and tenant preferences?

**Good answer:** A governed glossary keyed to domain IDs, tenant variants resolved centrally for all channels, automated checks for banned terms in source and translations, and a named owner who approves new terms.

**Red flags:**

- Same concept called different names on different screens.
- Tenant renaming that only affects the web UI.
- No glossary in the translation workflow.
- Terms invented per feature without review.

### `tenancy` Tenant-editable content safety

**Question:** What can a tenant change in this content, and what stops a tenant edit from removing required text, breaking translations, introducing unsafe markup or leaking into another tenant?

- Which strings are tenant-overridable, and which are locked (legal notices required by law, platform terms, security messages)?
- Is tenant-entered text treated as untrusted: escaped or sanitised, no script or arbitrary HTML, links checked?
- Do overrides exist in every active locale, and what is shown when a translation is missing (fallback language, with a flag to the tenant)?
- Is every override versioned and audited, with a preview before publishing and a way to roll back?
- Are overrides cached with the tenant ID in the key so one tenant's wording never appears for another?
- Can tenant copy break length limits (SMS segments, button widths, DLT-registered templates)?

**Good answer:** A defined list of overridable and locked strings, sanitised tenant input, locale completeness checks with a visible fallback, versioned and audited overrides with preview and rollback, tenant-scoped caching and enforced length limits per channel.

**Red flags:**

- Tenants able to edit or delete mandatory legal notices.
- Raw HTML accepted in tenant copy.
- Missing translations shown as string IDs.
- No audit trail of who changed wording that users relied on.

### `comprehension` Evidence that people understand

**Question:** What evidence shows that the intended readers, especially parties without lawyers, understand this content well enough to act correctly and on time?

- Which tasks were tested with real or representative users (for example file a reply, request an extension, pay a fee), with how many participants and in which languages?
- What were task success, error and time-to-complete rates, and what changed after testing?
- Are support tickets and secretariat queries tagged by the screen or message that caused confusion, and reviewed regularly?
- Are readability measures used as a signal only, alongside testing, rather than as the target?
- Is content tested with people with cognitive or learning disabilities and with older users?
- Are missed deadlines or wrong filings analysed for content causes?

**Good answer:** Named usability tests per major journey with participant profiles, measured task success and the copy changes made, plus ongoing signals from tagged support queries and process errors. Readability scores are tracked but not treated as proof of understanding.

**Red flags:**

- No testing with non-lawyer parties.
- A readability score as the only evidence.
- Support confusion not linked back to specific content.
- Content changes after launch never re-tested.

### `disclosure` Confidentiality and privacy in copy

**Question:** Could any message, notification, error or document produced in this scope disclose confidential case information or personal data to the wrong person or in the wrong place?

- What case detail appears in email subjects, SMS, WhatsApp and push previews that may be seen on lock screens or shared devices?
- Do error and empty-state messages reveal whether a case, party or document exists to someone without access?
- Do notifications to one party ever include another party's contact details, counsel's notes or sealed documents?
- Is the privacy notice for this journey itemised as DPDP Rules expect, available in the required languages, and shown before collection?
- Are templates that include variables tested so that a missing or wrong variable cannot pull in another case's data?
- Does copy in AI-generated summaries or drafts carry case content into logs or analytics?

**Good answer:** A per-channel rule on what case detail may appear outside the platform (reference only, no names or amounts), identical messages for not-found and no-access, tested template variables scoped to the case, and privacy notices in place and translated.

**Red flags:**

- Party names or claim values in SMS or email subjects.
- Different errors for 'does not exist' and 'no access'.
- Notifications built by string concatenation with unchecked variables.
- Privacy notice only in English where other languages are required.

### `provenance` Version and proof of what was shown

**Question:** If a party later disputes what they were told or agreed to, can we prove exactly which wording, in which language and version, they saw and accepted, and when?

- Is each declaration, consent, notice and confirmation stored with a version ID and locale alongside the action it relates to?
- Can the exact rendered text of a past version be reproduced, including tenant overrides that applied at that time?
- Are receipts and emails stored as sent, not regenerated from current templates?
- When legal text changes, are users who accepted earlier versions asked to re-accept where required, and is that rule defined per text?
- Is the audit record tamper-evident and retained for the case retention period?
- Is the authoritative language recorded when the user acted in a translation?

**Good answer:** Every legally significant acceptance records text version, locale, tenant override version and server timestamp in the audit trail, past versions can be rendered exactly, sent messages are archived as sent, and re-acceptance rules are defined.

**Red flags:**

- Only a boolean 'accepted terms' flag stored.
- Receipts regenerated from today's template.
- Tenant overrides not versioned.
- No record of the language shown.

### `localisation` Translation quality and process

**Question:** How is content in this scope translated, reviewed and kept in sync across languages, and how is quality assured for legal and procedural text?

- Which locales does each tenant need at launch, and who decides (tenant contract, DPDP language access, institutional rules)?
- Is machine translation used, and if so for which content classes, with what human review?
- Are translators given context (screenshots, notes, glossary, character limits) for every string?
- How is a source change propagated: are stale translations flagged and blocked from release?
- Is pseudo-localisation used in CI to catch hard-coded strings, truncation and concatenation?
- Are right-to-left and CJK layouts reviewed by a native reader before release?

**Good answer:** A locale plan per tenant, a translation workflow with glossary, context and length limits, human legal review for legal text, stale-translation detection blocking release, and pseudo-localisation in CI.

**Red flags:**

- Unreviewed machine translation of legal or procedural text.
- Translations shipped without context or glossary.
- Source changes that silently leave old translations live.
- No pseudo-locale testing.

### `ai-content` AI-generated and assisted text

**Question:** Where AI generates or suggests text in this scope (summaries, draft orders, suggested replies, auto-captions), is it clearly labelled, reviewed where it matters, and held to the same voice, terminology and accuracy rules?

- Which strings or outputs are AI-generated, and is each labelled so the reader knows (for example "AI summary — check against the documents")?
- Which AI outputs must be approved by a human before anyone else sees them (anything sent to parties or forming part of the record)?
- Do prompts enforce the glossary, voice and neutrality rules, and are outputs checked against them in evaluations?
- Can AI text ever appear as if written by the tribunal or the institution?
- Is AI text localised by the model or translated through the normal workflow, and who reviews it?
- How are users told the limits of AI summaries in plain language?

**Good answer:** An inventory of AI-generated content with labels, human approval for anything sent to parties or placed on the record, glossary and neutrality rules in prompts and evaluations, and clear plain-language limits shown to users.

**Red flags:**

- AI text sent to parties without review.
- No label distinguishing AI text from tribunal or institution text.
- AI outputs using terms outside the glossary.
- No evaluation of tone or neutrality.

