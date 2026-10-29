---
id: "APP-voice-tone-and-content-style"
title: "Voice, tone and content style guide"
parent: "APP-frontend-standards"
order: 7
type: "feature"
template: "content"
status: "draft"
owner: null
indicative: false
summary: "Platform voice principles, tone by situation, neutrality rules, microcopy patterns"
links: []
rev: 2
syncHash: "137f9ab465ba7b91"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.4.7 Voice, tone and content style guide

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Platform voice principles, tone by situation, neutrality rules, microcopy patterns

<!-- section:scope -->
## Scope and audiences

The platform's voice and style rules for every word users see on screens, emails, SMS, WhatsApp, generated PDFs (other than legal text owned by institutions), help content and API messages. Applies to CORD, TERES and HKIAC CMP surfaces in all route groups.

Readers:
| Reader | Legal knowledge | Likely state |
|---|---|---|
| Unrepresented parties (SEBI ODR investors, MSME claimants, consumers) | low | anxious, unfamiliar with procedure, often on a phone, may read in a second language |
| Counsel | high | busy, scanning, want precision |
| Neutrals | very high | careful, value neutrality and exact terms |
| Secretariat staff | high procedural knowledge | high volume, want short, consistent labels |
| Tenant and platform admins | technical or operational | configuring, need clear consequences |

<!-- section:voice -->
## Voice and tone

**Voice principles**
1. **Neutral.** The platform is a forum, not a side. Copy never favours a party, predicts an outcome, or praises or blames.
2. **Clear.** Plain words first, legal precision where it matters; one idea per sentence.
3. **Respectful.** Address people as adults; no jokes, emojis or exclamation marks in case surfaces.
4. **Informative, not advisory.** Say what the rules allow and what will happen; never tell someone what they should do in their case.
5. **Accountable.** Say who acts: "The tribunal will decide", "We will email you", "{tenantName} will review your request".

**Tone by situation**
| Situation | Tone | Example |
|---|---|---|
| Routine task | brief, neutral | "Add a document" |
| Deadline near | direct, specific, calm | "You can file your response until 5 March 2026, 17:00 Singapore time." |
| Something failed | calm, own it if it is ours | "We could not save your changes. Try again." |
| Legal step with consequence | formal, exact, no softening | "When you submit, your Statement of Claim will be sent to the respondent and the tribunal. You cannot change it after that." |
| Award or outcome published | neutral, factual, no congratulation or sympathy | "The tribunal has issued the final award." |
| Admin consequence | explicit about scope | "This change applies to all new cases from today. Cases already open keep their current rules." |

<!-- section:terminology -->
## Terminology and glossary alignment

Canonical terms come from [[I18N-platform-glossary-and]]; tenant variants through [[PKG-tenant-terminology-and-copy]].

| Concept (domain ID) | Canonical term | Allowed variants (by tenant or procedure) | Do not use |
|---|---|---|---|
| Case | case | matter, dispute, complaint (consumer) | file, ticket, lawsuit |
| Party initiating | claimant | applicant, complainant | plaintiff (unless tenant rules use it) |
| Party responding | respondent | opposite party (consumer) | defendant, accused |
| Representative | representative / counsel | advocate, lawyer, authorised representative | agent (ambiguous) |
| Neutral | arbitrator, mediator, conciliator (show the role) | presiding arbitrator, sole arbitrator | judge, "the neutral" in user copy |
| Tribunal | tribunal | arbitral tribunal | court (unless a court tenant) |
| Secretariat staff | case manager, tribunal secretary | registry | admin (for case staff) |
| Filing | filing (noun), file / submit (verb for filings) | submission | upload (for filings) |
| File on a device | file, document | exhibit (when in evidence) | attachment (in case surfaces) |
| Hearing bundle | bundle | eBundle | binder, pack |
| Procedural order | procedural order | direction | ruling |
| Award | award | final award, partial award, settlement agreement (mediation) | judgment, decision (for awards) |
| Deadline | deadline / "until {date time zone}" | time limit | due date (for legal deadlines) |
| Notice served | notice, served | delivered (for proof) | sent (when legal service is meant) |

<!-- section:patterns -->
## Microcopy patterns

| Pattern | Rule | Good | Bad |
|---|---|---|---|
| Buttons | verb + object, sentence case, ≤ 3 words where possible | "Submit filing", "Add document" | "OK", "Click here", "Submit Now!" |
| Consequential buttons | name the exact effect | "Issue procedural order", "Pay ₹12,500" | "Confirm", "Proceed" |
| Links | describe the destination | "View the case timeline" | "Read more" |
| Field labels | noun phrase, no colon; hints below label | "Respondent's email address" + hint "We will send the notice here." | "Email*:" |
| Required / optional | mark optional fields "(optional)"; most fields are required | "Middle name (optional)" | asterisks only |
| Empty state | what will appear + why empty + next step | "No documents yet. Documents filed in this case will appear here." | "Nothing here!" |
| Confirmation dialog | heading states the action and object; body states consequence | "Withdraw your claim?" / "The tribunal and the respondent will be told. You cannot undo this." | "Are you sure?" |
| Success | say what happened and what comes next | "Filing submitted. Your receipt number is F-2026-00451. The tribunal has been notified." | "Success!" |
| Status labels | from the state machine labels, never raw enum names | "Awaiting response" | "AWAITING_RESPONSE" |
| Dates and times | absolute date, 24-hour time, seat time zone, local time when different | "5 March 2026, 17:00 Singapore time (14:30 your time)" | "05/03/26 5pm", "in 3 days" alone |
| Money | currency symbol or code with locale grouping | "₹1,25,000.00", "SGD 4,500.00" | "125000 INR" |
| Numbers in copy | numerals for 10 and above, and for all dates, amounts and deadlines | "7 days", "15 documents" | "seven days" for deadlines |

<!-- section:errors -->
## Error messages

Error copy follows the structure and catalogue in [[APP-error-message-catalogue]].

<!-- section:legal -->
## Legal and declaration text

This guide does not own legal text. Declarations, consents, privacy notices, terms and service wording are owned by Nomology legal or by the institution's rules and recorded with versions in [[I18N-legal-declaration-and-consent]] and [[SEC-privacy-notice-copy]]. Copy around legal text (introductions, button labels) must not change its meaning; for example, the button under a statement of truth reads "I confirm and submit", not "Continue".

<!-- section:notifications -->
## Notifications and generated documents

Notification copy follows [[PKG-notification-copy]]: subject lines say who and what without case content beyond the case reference ('New procedural order in case ARB-2026-00123'); no party names or amounts in SMS, WhatsApp or push previews.

<!-- section:plain -->
## Plain language for non-lawyer parties

For party journeys: sentences under 20 words on average, active voice, explain a legal term the first time it appears on a screen ('The respondent — the person or company the claim is against — has 14 days to reply'), examples where they help, but keep the exact procedural terms that the rules use. Detailed rules and comprehension testing in [[DOC-plain-language-guidance-for]], following ISO 24495-1 principles [R1].

<!-- section:localisation -->
## Localisation readiness

Write source copy that translates: no idioms, no concatenated strings, ICU plurals and select for gender or role, allow 30–40% expansion in UI layouts [R2]. Translators receive screenshots and glossary terms.

<!-- section:accessibility -->
## Accessible content

Headings describe the content below; link and button text makes sense out of context; instructions do not rely on shape, colour or position; alt text for meaningful images says what the image shows; language changes are marked. Content for people with cognitive disabilities follows the W3C COGA guidance on clear, predictable content [R3].

<!-- section:governance -->
## Content governance and workflow

- Owner: content lead (UX). Reviewers: legal for anything describing rights, deadlines or consequences; product for persona fit; accessibility lead for accessible content rules.
- Strings live in `packages/messages/{namespace}/en.json`; changes ship with code. Tenant overrides are content changes without a deploy, through [[PKG-tenant-terminology-and-copy]] with preview, version history and audit.
- A copy linter runs in CI on message catalogues: banned terms, exclamation marks, "click here", sentence case, maximum lengths.

<!-- section:questions -->
## Open questions

- [ ] Spelling standard: British English (proposed, consistent with Indian and Singapore usage) or US English for US tenants (owner: content lead)
- [ ] Should neutrals' role names be tenant-configurable (for example "Sole Arbitrator" vs "Arbitrator") (owner: product)
- [ ] Who approves tenant overrides that change procedural meaning (owner: legal with the tenant)

<!-- checks -->
## Template checks

<!-- check:legal-accuracy -->
### Legal meaning and approval

The guide separates owned legal text from surrounding copy; copy around legal text is reviewed by legal; numbers in deadlines and fees come from the rules engine; the 'informative, not advisory' principle is a review item for every party-facing screen.

<!-- check:terminology -->
### Terminology consistency

Canonical terms and banned synonyms are listed here and enforced by a catalogue linter; tenant variants are applied through one override mechanism so they reach screens, emails and PDFs together.

<!-- check:tenancy -->
### Tenant-editable content safety

Tenants can change terminology variants and selected copy only through the override package, which keeps locked strings, sanitises input and versions every change.

<!-- check:comprehension -->
### Evidence that people understand

Party journeys are tested with representative users before Approved (see [[DOC-plain-language-guidance-for]]); readability scores are used as a signal only.

<!-- check:ai-content -->
### AI-generated and assisted text

AI-generated text follows the same voice and neutrality rules and is labelled as AI-generated until a person accepts it ([[AI-ai-generated-text-labelling-and]]); AI text never appears as if written by the tribunal before it is approved.

<!-- citations -->
## Citations

```json
[
  {
    "body": "ISO",
    "id": "R1",
    "ident": "ISO 24495-1:2023",
    "kind": "standard",
    "title": "Plain language — Part 1: Governing principles and guidelines",
    "url": "https://www.iso.org/standard/78907.html"
  },
  {
    "body": "W3C Internationalization",
    "id": "R2",
    "kind": "standard",
    "title": "Text size in translation",
    "url": "https://www.w3.org/International/articles/article-text-size.en.html"
  },
  {
    "body": "W3C",
    "id": "R3",
    "kind": "standard",
    "title": "Making Content Usable for People with Cognitive and Learning Disabilities",
    "url": "https://www.w3.org/TR/coga-usable/"
  }
]
```

<!-- end -->
