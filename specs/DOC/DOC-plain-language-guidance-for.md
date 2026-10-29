---
id: "DOC-plain-language-guidance-for"
title: "Plain-language guidance for unrepresented parties"
parent: "DOC-tenant-facing-help-centre"
order: 1
type: "feature"
template: "content"
status: "draft"
owner: null
indicative: false
summary: "Reading targets, inline explanations of legal terms, journey copy for SEBI ODR investors and MSME claimants, comprehension testing"
links: []
rev: 2
syncHash: "bfd2c8e3dcc6d804"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 17.4.1 Plain-language guidance for unrepresented parties

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Reading targets, inline explanations of legal terms, journey copy for SEBI ODR investors and MSME claimants, comprehension testing

<!-- section:scope -->
## Scope and audiences

Governs the words parties without lawyers see in their journeys: screens in the `(counsel)` route group when used by a self-represented party ([[APP-party-and-counsel-portal]]), notices and emails sent to them, the party-facing help articles ([[DOC-tenant-facing-help-centre]]) and the explanations of legal terms. Primary readers:

| Reader | Likely situation |
|---|---|
| SEBI ODR investor (via an ODR institution tenant) | Complaint against a market participant; may be older, on a phone, reading English as a second language |
| MSME claimant | Small business owner chasing payment; busy, possibly first dispute |
| Consumer or individual in a CORD tenant | First contact with dispute resolution; anxious about cost and consequences |
| Respondent who received a notice unexpectedly | May be suspicious that the notice is a scam; needs to verify and understand deadlines |

The goal is that these readers can find what they need, understand it and act on it correctly and on time [R1].

<!-- section:voice -->
## Voice and tone

- **Calm, clear and neutral.** The platform is a neutral forum; copy never takes a side, never predicts outcomes, never tells a party what they should decide.
- **Explain, do not advise.** Say what a step is and what happens next; do not say whether it is a good idea. Where advice is needed, point to sources of help (the tenant's helpdesk, legal aid where the tenant provides a link).
- **Respectful.** No blame ("You failed to…"); state facts ("We did not receive your reply by {dueAt}").
- **Tone by situation**: welcoming at first contact; precise and calm for deadlines; plain and non-alarming for consequences ("If you do not reply, the case may continue without your reply").

<!-- section:terminology -->
## Terminology and glossary alignment

Legal terms stay precise, and each is explained the first time it appears on a screen, with the explanation also in the glossary ([[I18N-platform-glossary-and]]).

| Term (canonical) | First-use explanation (final copy, English) | Avoid |
|---|---|---|
| Claimant | "the person or business that started this case" | plaintiff, complainant (unless it is the tenant's variant) |
| Respondent | "the person or business the case is against" | defendant, accused |
| Neutral | "the independent person who helps resolve the case ({neutralRole})" | judge |
| Conciliation | "a meeting where an independent conciliator helps both sides try to agree" | settlement talks |
| Arbitration | "a process where an independent arbitrator decides the dispute after hearing both sides" | court case, trial |
| Award | "the arbitrator's written decision" | judgment, verdict |
| Notice | "an official message about this case" | letter, alert |
| Deadline | "the last date and time to do this. After this time, you may not be able to do it." | due date (alone) |
| Filing | "documents you send to the case" | submission |

Procedure variants (for example how a SEBI ODR matter moves from conciliation to arbitration) are taken from the tenant's rules and confirmed by legal, not written from memory.

<!-- section:patterns -->
## Microcopy patterns

| Pattern | Rule | Good | Bad |
|---|---|---|---|
| Page heading | Say the task | "Reply to the claim" | "Respondent submission portal" |
| Step intro | One sentence on why and by when | "Tell us your side of the dispute by 17:00 IST on 14 November 2026." | "Pursuant to the rules, the respondent may submit a reply." |
| Deadline display | Date, time, time zone, and time left | "Due by 17:00 IST, Friday 14 November 2026 (6 days left)" | "Due 14/11" |
| Buttons | Verb + object | "Send my reply" | "Submit" |
| Consequence text | Plain, factual, not alarming | "After you send your reply, you cannot change it. You can send more documents later if the neutral allows it." | "WARNING: irreversible action!" |
| Optional help | Collapsible "What does this mean?" under terms | "What is an award?" | Long legal paragraph inline |
| Confirmation | What happened, reference, what next | "Your reply was sent at 15:42 IST. Reference RPL-7F3K. We emailed you a copy. The neutral will review it." | "Success" |

**Reading targets** (proposed): sentences average under 20 words; one idea per sentence; active voice; common words. Readability scores (for example Flesch-Kincaid) are tracked as a signal only; comprehension testing decides.

<!-- section:errors -->
## Error messages

Party-facing errors follow [[APP-error-message-catalogue]] with this extra rule: say what happened and what to do now, in that order, and never only a code.

| Code | Final copy |
|---|---|
| `deadline-passed` | "The deadline to reply was 17:00 IST on 14 November 2026. You can ask for more time. The neutral will decide." + button "Ask for more time" (only if the tenant's rules allow requests) |
| `upload-too-large` | "This file is larger than {maxSize}. Split it into smaller files, or send a link if your institution allows it." |
| `upload-blocked` | "We could not accept this file because our security check found a problem. Try another copy of the file." |
| `session-expired` | "You were signed out to keep your case safe. Sign in again. Your draft was saved." |
| `not-found` | "We cannot find this page. It may have moved, or you may not have access. Go to your cases." |
| `payment-failed` | "Your payment did not go through. You have not been charged. Try again or use another method." |

<!-- section:legal -->
## Legal and declaration text

Texts with legal effect in party journeys, each listed in the register [[I18N-legal-declaration-and-consent]]:

| Text | Owner | Approver |
|---|---|---|
| Statement of truth / declaration on filing | Tenant (institution rules) | Tenant legal; Nomology legal for platform wording |
| Consent to electronic service and communication | Tenant | Tenant legal; Nomology legal |
| Privacy notice for the journey | Data fiduciary / controller for that tenant | Nomology legal and the tenant ([[SEC-privacy-notice-copy]]) |
| Consequence statements (what happens if you do not reply) | Tenant rules | Tenant legal |

When simplifying legal text, the simplified version is reviewed by the approver to confirm it has not changed the legal meaning; where a precise legal text must be shown, the plain explanation sits beside it, and the screen states which text governs.

<!-- section:plain -->
## Plain language for non-lawyer parties

- Use the reader's words: "the person or business you have a dispute with" before introducing "respondent".
- Introduce each legal term once with a short explanation and a "What does this mean?" link.
- Give an example where a step is unfamiliar ("For example: invoices, emails, contracts, photos").
- Keep precise: dates, times, amounts, names of the neutral and institution, and consequences are never simplified away.
- Respondents receiving a first notice get a "Is this message genuine?" explanation with a way to verify the case on the institution's official site.
- Never use fear or urgency beyond the facts.

<!-- section:localisation -->
## Localisation readiness

Party journeys are launched per locale only after translation by qualified legal translators, glossary alignment in translation memory, and comprehension testing in that language. For India, notice and consent content is offered in English or a language of the Eighth Schedule to the Constitution as the DPDP Act requires for notices [R2]; which further languages each tenant needs is set per tenant ([[I18N-l10n]]). The authoritative language of each legal text is stated on screen.

<!-- section:accessibility -->
## Accessible content

Follows WCAG 2.2 AA and the cognitive accessibility patterns of W3C COGA [R3]: clear headings, one task per page in wizards, help in a consistent place, no time limits without extension, and plain language for instructions and errors.

<!-- section:governance -->
## Content governance and workflow

Content design writes; the product owner and Nomology legal review; tenant legal approves tenant-owned texts. Comprehension testing (at least 5 representative participants per journey per launch locale, proposed) is done before launch and after major changes; findings and changes are recorded. Support tickets and secretariat queries are tagged with the screen that caused confusion and reviewed monthly.

<!-- section:questions -->
## Open questions

- [ ] Confirm reading targets with product and legal.
- [ ] Confirm the procedural description for SEBI ODR matters (conciliation and arbitration stages) against the current SEBI circular and each ODR institution tenant's rules.
- [ ] Which languages are needed for MSME claimants at launch?
- [ ] Recruitment route for comprehension testing participants (investors, MSMEs) in each language.

<!-- checks -->
## Template checks

<!-- check:legal-accuracy -->
### Legal meaning and approval

Every legal text in party journeys has an owner and approver (Legal table); simplifications are re-approved by that approver; numbers (deadlines, fees) come from tenant rules and calendars; procedure descriptions come from tenant rules confirmed by legal.

<!-- check:terminology -->
### Terminology consistency

Terms and first-use explanations are tied to the glossary; banned synonyms (plaintiff, judge, verdict) are linted in the message catalogue.

<!-- check:comprehension -->
### Evidence that people understand

Comprehension testing with at least 5 representative participants per journey per locale before launch, plus monthly review of support tickets tagged by screen; readability scores are a signal only.

<!-- check:disclosure -->
### Confidentiality and privacy in copy

Party-facing errors and empty states do not reveal whether other cases or parties exist; first-notice copy explains how to verify a notice without disclosing case details to someone who has not signed in.

<!-- check:localisation -->
### Translation quality and process

Legal translators, translation memory with glossary, comprehension testing per locale, and on-screen statement of the authoritative language; India notice languages follow the DPDP Act notice-language option.

<!-- citations -->
## Citations

```json
[
  {
    "body": "ISO",
    "excerpt": "Communication is in plain language when readers can find what they need, understand it and use it.",
    "id": "R1",
    "ident": "ISO 24495-1",
    "kind": "standard",
    "title": "Plain language — Part 1: Governing principles and guidelines",
    "url": "https://www.iso.org/standard/78907.html",
    "version": "2023"
  },
  {
    "clause": "Section 5(3)",
    "excerpt": "The Data Fiduciary shall give the Data Principal the option to access the notice and consent request in English or any language specified in the Eighth Schedule to the Constitution.",
    "id": "R2",
    "issuer": "Government of India (MeitY)",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
  },
  {
    "body": "W3C",
    "excerpt": "Design patterns such as clear words, short sentences, explained terms and consistent help for people with cognitive and learning disabilities.",
    "id": "R3",
    "ident": "Making Content Usable for People with Cognitive and Learning Disabilities",
    "kind": "standard",
    "title": "Making Content Usable for People with Cognitive and Learning Disabilities",
    "url": "https://www.w3.org/TR/coga-usable/"
  }
]
```

<!-- end -->
