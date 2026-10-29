---
id: "APP-error-message-catalogue"
title: "Error message catalogue"
parent: "APP-error-boundaries-loading-and"
order: 1
type: "requirement"
template: "content"
status: "draft"
owner: null
indicative: false
summary: "Error codes, structure and final copy for UI and API errors; identical not-found / no-access text"
links: []
rev: 2
syncHash: "7f8ae7dff046d795"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.4.3.1 Error message catalogue

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Error codes, structure and final copy for UI and API errors; identical not-found / no-access text

<!-- section:scope -->
## Scope and audiences

Every error message users can see in `apps/web` (inline field errors, alerts, error pages, toasts) and the human-readable `title` and `detail` text of API problems ([[APP-api-error-catalogue-problem]]). Readers range from counsel who file daily to first-time investors and MSME claimants on phones, often anxious because a deadline is near. Developer-facing wording of the public API is coordinated with [[DOC-developer-facing-api-copy]]. Not in scope: notification copy ([[PKG-notification-copy]]).

<!-- section:voice -->
## Voice and tone

Errors follow [[APP-voice-tone-and-content-style]]: calm, specific, never blaming. Tone when a deadline is involved: direct and factual, with the exact date and time and what can still be done. Never suggest that a party is likely to win or lose because of the error, and never give legal advice ('You should file a reply' is advice; 'You can file a reply until 5 March 2026, 17:00 Singapore time' is information).

<!-- section:terminology -->
## Terminology and glossary alignment

Errors use glossary terms from [[I18N-platform-glossary-and]] and tenant variants from [[PKG-tenant-terminology-and-copy]] (for example `{case}` resolves to 'case' or 'matter'). Never use internal words in messages: 'tenant', 'record', 'entity', 'workflow', 'RLS', 'invalid state', 'null', 'server'.

<!-- section:patterns -->
## Microcopy patterns

Structure for every message:
1. **What happened**, in plain words ("We could not upload 'Exhibit C.pdf'.")
2. **Why**, only if it helps the user act ("The file is larger than 500 MB.")
3. **What to do now** ("Split the file or upload a compressed copy.")

Rules:
- Field errors name the field and the fix: "Enter an email address in the format name@example.com", not "Invalid input".
- Put the message next to the field and in the error summary; the summary heading is "There is a problem".
- Never only colour or an icon; always text.
- Never show raw codes as the main message; show the support reference in small print: "Reference: 0192F6C4" (first 8 characters of the request ID).
- Never say "Oops", "Something went wrong" alone, "Error 500", or exclamation marks.
- Use 'we' for the platform and the institution's name for the institution's decisions ("HKIAC has not yet accepted…" via tenant name variable).

<!-- section:errors -->
## Error messages

Catalogue (final English copy; variables in ICU syntax). `code` links to the problem type in [[APP-api-error-catalogue-problem]].

| Code | Problem type | Where | Message | Action shown |
|---|---|---|---|---|
| `NOT_FOUND` | not-found | entity pages (also used for no access) | **We cannot find this page.** It may have been moved, or the link may be wrong. If you were sent this link, check that you are signed in with the email address it was sent to. | Go to my {cases} · Contact support |
| `AREA_NO_ACCESS` | action-not-permitted | persona shell | **You do not have access to this area.** Your account does not have the {role} role for {tenantName}. | Go to my other areas · Ask your administrator |
| `SESSION_EXPIRED` | session-expired | sign-in notice | **You were signed out to protect your account.** Sign in again to continue. Anything you were writing has been saved. | Sign in |
| `STEP_UP_REQUIRED` | step-up-required | dialog | **Confirm it is you.** For your security, enter a new code before you {action}. | Continue |
| `RATE_LIMITED` | rate-limited | inline | **Too many attempts.** Try again in {minutes, plural, one {# minute} other {# minutes}}. | — |
| `FILING_STAGE_CLOSED` | business-rule-violation | filing stepper | **You can no longer file a {filingType} in this {case}.** The time to file ended on {deadline}. You can ask the tribunal for more time. | Ask for more time |
| `FILING_NOT_YET_OPEN` | business-rule-violation | filing stepper | **You cannot file a {filingType} yet.** This becomes possible after {event}. | View {case} timeline |
| `DRAFT_VERSION_CONFLICT` | version-conflict | stepper, editors | **This draft was changed in another window.** Choose which version to keep. | Load latest · Keep mine as a copy |
| `VERSION_CONFLICT` | version-conflict | secretariat rows, admin | **Someone else updated this just now.** We have loaded the latest version. Check it and try again. | — |
| `INVALID_STATE_TRANSITION` | invalid-state-transition | secretariat dialog | **This {case} cannot move to "{target}" from "{current}".** Allowed next steps: {allowedList}. | — |
| `UPLOAD_TOO_LARGE` | payload-too-large | dropzone | **'{fileName}' is too large.** Files can be up to {maxSize}. Split the file or upload a compressed copy. | Choose another file |
| `UPLOAD_TYPE_NOT_ALLOWED` | unsupported-media-type | dropzone | **'{fileName}' is not a file type we accept.** Upload a PDF, Word document, image or audio file. | Choose another file |
| `UPLOAD_MALWARE` | file-rejected | dropzone | **We removed '{fileName}' because it may contain a virus.** Check the file on your device and upload a clean copy. | Choose another file |
| `UPLOAD_FAILED` | dependency-unavailable / network | dropzone | **'{fileName}' did not finish uploading.** Check your connection and try again. Your other files are safe. | Retry |
| `PAYMENT_FAILED` | business-rule-violation | payment return | **Your payment did not go through.** You have not been charged. Try again or use another payment method. | Try again |
| `PAYMENT_PENDING` | — | payment return | **We are waiting for your bank to confirm the payment.** This can take up to {minutes} minutes. We will email you when it is confirmed. Do not pay again. | Go to {case} |
| `HEARING_NOT_OPEN` | business-rule-violation | room | **The hearing room opens at {openTime}.** The hearing starts at {startTime}. | Test my camera and microphone |
| `MEDIA_PERMISSION_DENIED` | — | room | **Your browser is blocking your camera or microphone.** Allow access for this site in your browser settings, or join by phone. | How to allow access · Join by phone |
| `OFFLINE` | — | global banner | **You are offline.** We will try again when you are back online. Do not close this page. | — |
| `SERVER_ERROR` | internal-error | error boundary | **We could not load this page.** This is a problem on our side. Try again in a few minutes. If it keeps happening, contact support and quote the reference below. | Try again · Contact support |
| `SECTION_ERROR` | internal-error | section boundary | **We could not load this section.** The rest of the page is working. | Try again |
| `SERVICE_UNAVAILABLE` | dependency-unavailable | inline | **{serviceName} is not available at the moment.** Try again later. Nothing has been sent. | — |
| `TENANT_SUSPENDED` | tenant-suspended | full page | **This service is not available at the moment.** Contact {tenantName} for help. | — |
| `INVITATION_EXPIRED` | business-rule-violation | invite page | **This invitation has expired.** Ask {inviterOrg} to send a new one. | — |
| `SIGN_IN_LINK_SENT` | — | sign-in | If an account exists for {email}, we have sent a sign-in link. It works for 15 minutes. | Resend link |
| `OTP_INCORRECT` | validation-failed | sign-in | **The code is not correct.** Check the latest message we sent and try again. | Send a new code |
| `AI_UNAVAILABLE` | dependency-unavailable | neutral AI panel | **Drafting help is not available for this {case}.** You can keep writing as normal. | — |

**Identical not-found and no-access text**: `NOT_FOUND` is the only message used for both an unknown and a forbidden case, document, filing or hearing; HTTP status (404), heading and layout are identical, so the message cannot be used to learn whether a case exists.

<!-- section:legal -->
## Legal and declaration text

Errors with legal effect: `FILING_STAGE_CLOSED`, `FILING_NOT_YET_OPEN`, `PAYMENT_PENDING` and `PAYMENT_FAILED`, `INVITATION_EXPIRED`. Their wording about deadlines and consequences is approved by Nomology legal and checked against each tenant's rules where the tenant overrides it. Deadline values are inserted from the rules engine ([[PKG-calendars-and-deadline]]), never typed into strings. Messages never state that a deadline cannot be extended; they point to the request route.

<!-- section:plain -->
## Plain language for non-lawyer parties

Party-facing errors aim at a reading age of about 9 to 11 years (guidance, not a hard rule; see [[DOC-plain-language-guidance-for]]): short sentences (under 20 words), common words, no Latin, explain any legal term in the same sentence.

<!-- section:localisation -->
## Localisation readiness

Messages are externalised with stable IDs (`errors.FILING_STAGE_CLOSED.title`, `.body`, `.action`) in ICU MessageFormat [R1] with translator notes and character limits (titles ≤ 60 characters in English; allow 40% expansion). Variables are named, never positional. The English text is the source; in a tenant's legal language pair, the tenant's rules decide which version is authoritative.

<!-- section:accessibility -->
## Accessible content

Messages are programmatically associated with their fields; summary links move focus to the field; messages make sense out of context for screen-reader users; no message relies on colour or position ('the red box above').

<!-- section:governance -->
## Content governance and workflow

Owner: content lead. New codes are added by pull request to `packages/messages/errors/*.json` with a matching problem type; lint fails if a code has no English copy, no translator note or uses a banned word. Tenants may override wording of selected codes (not `NOT_FOUND`, `SESSION_EXPIRED`, security messages) through [[PKG-tenant-terminology-and-copy]].

<!-- section:questions -->
## Open questions

- [ ] Legal approval of the deadline-related messages (owner: legal)
- [ ] Which codes tenants may override (proposed: filing and payment messages only) (owner: product)
- [ ] Support contact shown in messages: tenant's or Nomology's? Proposed: tenant's for case matters, Nomology's for technical faults (owner: operations)

<!-- checks -->
## Template checks

<!-- check:legal-accuracy -->
### Legal meaning and approval

Deadline and consequence messages take values from the rules engine, are approved by legal, and point to the request route instead of stating that time cannot be extended.

<!-- check:terminology -->
### Terminology consistency

Messages use glossary terms with tenant variables (`{case}`, `{filingType}`); internal words are banned by a lint rule on the message catalogue.

<!-- check:tenancy -->
### Tenant-editable content safety

Overrides are allowed only for listed codes, stored per tenant and version, and sanitised; locked codes (not-found, session and security messages) cannot be changed so the identical not-found behaviour holds.

<!-- check:disclosure -->
### Confidentiality and privacy in copy

`NOT_FOUND` is shared by unknown and forbidden entities; messages never include other parties' names or whether a document exists; support references are request ID fragments, not personal data.

<!-- check:localisation -->
### Translation quality and process

ICU messages with stable IDs, translator notes and length limits; pseudo-localisation in CI catches hard-coded strings and truncation.

<!-- citations -->
## Citations

```json
[
  {
    "body": "Unicode ICU",
    "id": "R1",
    "kind": "standard",
    "title": "ICU User Guide: Formatting Messages",
    "url": "https://unicode-org.github.io/icu/userguide/format_parse/messages/"
  }
]
```

<!-- end -->
