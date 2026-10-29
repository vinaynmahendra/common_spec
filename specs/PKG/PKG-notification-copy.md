---
id: "PKG-notification-copy"
title: "Notification copy"
parent: "PKG-notifications"
order: 2
type: "feature"
template: "content"
status: "draft"
owner: null
indicative: false
summary: "Email, SMS (DLT-registered templates in India), WhatsApp and push copy; lock-screen-safe rules; length limits"
links: []
rev: 2
syncHash: "d613deef9a12a41c"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 5.11.2 Notification copy

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Email, SMS (DLT-registered templates in India), WhatsApp and push copy; lock-screen-safe rules; length limits

<!-- section:scope -->
## Scope and audiences

Copy for every notification sent by [[PKG-notifications]]: email (subject, preheader, body), SMS (India DLT-registered templates, Singapore and US plain SMS), WhatsApp (Meta-approved templates), web push and in-app notifications. Readers: parties (often unrepresented investors or MSME owners, reading on a phone, possibly anxious about a dispute), counsel, neutrals, secretariat staff and transcribers. Notices with legal effect (service of notice of arbitration, orders, awards) also follow [[DOM-service-of-notices-and-proof]]. Preferences and non-opt-out rules are in [[PKG-notification-preferences]]; provider mechanics in [[INT-messaging-providers]].

<!-- section:voice -->
## Voice and tone

Neutral, factual and short. A notification says what happened, what the reader needs to do and by when, and where to do it. It never favours a party, predicts an outcome, or gives legal advice. Tone shifts: deadline reminders are calm and specific; failed payments and rejected filings are direct with a next step; awards and orders state the fact only ("An award has been issued in your case"), with no adjectives. Follow [[APP-voice-tone-and-content-style]].

<!-- section:terminology -->
## Terminology and glossary alignment

Use canonical glossary terms ([[I18N-platform-glossary-and]]) with tenant variants from [[PKG-tenant-terminology-and-copy]]: "case" (tenant variant "matter"), "statement of claim", "procedural order", "award", "hearing", "deadline". In SMS and push, use the tenant's short name and the case reference, not party names. Banned: "lawsuit", "judge" (for arbitrators), "verdict", "you won / lost".

<!-- section:patterns -->
## Microcopy patterns

| Element | Rule | Good | Bad |
|---|---|---|---|
| Email subject | Event + case reference, under 70 characters, no party names | "Hearing scheduled · ARB-2026-0142" | "Mr X v. Y Ltd: important update!!" |
| Preheader | One line of what to do next | "Join on 4 Nov at 9:00 am SGT. Details inside." | Repeat of subject |
| Body opening | What happened, in one sentence | "A procedural order has been issued in case ARB-2026-0142." | "We are pleased to inform you…" |
| Call to action | One primary link, verb-first | "View the order" | "Click here" |
| Date and time | Absolute, weekday, recipient's time zone, plus defining zone if different | "Friday 7 November 2026, 5:00 pm IST (7:30 pm SGT)" | "in 3 days" |
| Footer | Tenant name, why you received it, how to change preferences (unless non-optional), help link | | |

<!-- section:errors -->
## Error messages

Notifications about failures follow the error pattern: what happened, what to do. Examples: "Your payment of INR 25,000 for case ARB-2026-0142 did not go through. You can try again before Friday 7 November 2026." / "Your filing could not be accepted because a document failed the security check. Upload a new copy before the deadline." Never include provider error codes or internal reasons. Codes come from [[APP-error-message-catalogue]].

<!-- section:legal -->
## Legal and declaration text

| Text | Owner | Approver | Versioned |
|---|---|---|---|
| Notice of arbitration / service notice wording | Tenant (institutional rules) | Tenant legal | Yes, with template version recorded on each sent notice |
| "Deemed received" or service statements | Tenant rules | Tenant legal + Nomology legal review | Yes |
| Footer: why you received this, privacy link | Nomology legal | Nomology legal | Yes |
| Opt-out wording for optional channels | Nomology legal | Nomology legal | Yes |
| DLT-registered SMS templates (India) | Nomology (as sender entity for the tenant, assumption) | Registered on the DLT platform | Template ID stored per message |

Every sent message is stored as sent (rendered body, template ID and version, locale), not regenerated, so proof of what was sent is available ([[DOM-service-of-notices-and-proof]]).

<!-- section:notifications -->
## Notifications and generated documents

**Lock-screen-safe rule.** SMS, WhatsApp and push previews can be seen by others. They may contain only: the tenant's short name, the event type in generic words, the case reference, a date and a link. They must not contain: party names, amounts claimed, allegations, award outcomes, document titles, or contact details of other parties.

| Channel | Limits and rules | Example |
|---|---|---|
| Email | Subject under 70 characters; body plain HTML with text alternative; no attachments with case content (links to the platform instead); one primary link | Subject "Response due 7 Nov · ARB-2026-0142" |
| SMS (India) | Must match a DLT-registered content template exactly, with variables in the registered positions (`{#var#}`), from a registered header; keep within one segment where possible (160 GSM-7 characters, or 70 in Unicode for Indian scripts) | "{#var#}: A new document is available in case {#var#}. View it at {#var#} -{#var#}" |
| SMS (Singapore, US) | One segment preferred; sender ID rules per country; include opt-out instruction where required for optional messages | "Institution: Hearing on 4 Nov 9:00am SGT for ARB-2026-0142. Details: https://..." |
| WhatsApp | Utility-category template approved by Meta; variables only in approved positions; no marketing content; only to users who opted in | "There is an update in your case {{1}}. Open the platform to view it: {{2}}" |
| Push | Title up to 40 characters, body up to 100; no case content beyond the reference | "Deadline tomorrow · ARB-2026-0142" |
| In-app | Can include document titles and party roles, because it is behind sign-in and permissions | "Statement of Defence filed by Respondent" |

Assumption: DLT variable length limits and template categories (service implicit, service explicit, transactional) vary by operator platform; to be confirmed with the SMS provider and legal before templates are registered. Changing an Indian SMS template requires re-registration, so SMS copy changes are planned with lead time.

**Generated documents.** Emails link to generated PDFs; PDF copy rules are in the document templates node [[PKG-document-and-notification]].

<!-- section:plain -->
## Plain language for non-lawyer parties

Party-facing notifications target a reading age of about 12 to 14 years in English (used as a signal, not a target; comprehension testing decides). One idea per sentence, under 20 words where possible. Legal terms are named and explained on the linked page, not in the SMS. Must stay precise: dates, times, amounts, case references and what happens if the reader does nothing, as stated in the tenant's rules. Follow [[DOC-plain-language-guidance-for]].

<!-- section:localisation -->
## Localisation readiness

Each template has a stable ID (`notif.hearing.scheduled.email.subject`) and ICU MessageFormat with named variables and plurals [R1]. Translator notes give channel, character limit and lock-screen rule. Locales per tenant from tenant settings; the recipient's preferred language is used, falling back to the tenant default, then English. For DLT SMS, each language version is a separately registered template. The authoritative language for notices with legal effect is set by the tenant's rules and recorded with the message.

<!-- section:accessibility -->
## Accessible content

Emails: real text (no text in images), semantic headings, link text that makes sense out of context ("View the order", not "Click here"), `lang` attribute set to the message language, minimum 14 px body text, contrast as per tokens, works with images off and in dark-mode email clients. SMS: avoid abbreviations screen readers misread; write times as "9:00 am" not "0900h".

<!-- section:governance -->
## Content governance and workflow

Copy lives in `packages/notifications/templates/{templateId}/{locale}.mf` with metadata (channel, owner, legal class, DLT template ID). Changes go through PR review by content design; legal-class templates also need Nomology legal approval; tenant-owned notice wording is edited in tenant admin through [[PKG-document-and-notification]] with preview and version history. SMS and WhatsApp template changes include the external registration or approval step before release.

<!-- section:questions -->
## Open questions

- [ ] Which entity registers DLT headers and templates in India: NTPL for all tenants, or each tenant as principal entity (owner: legal, COO).
- [ ] Confirm the DLT template categories and variable limits with the chosen SMS provider (owner: integrations lead).
- [ ] Which languages are needed at launch for SEBI ODR investor notifications (owner: product).
- [ ] May email subjects include the case title for counsel and neutrals if a tenant asks (proposed: no, reference only) (owner: security lead, legal).

<!-- checks -->
## Template checks

<!-- check:legal-accuracy -->
### Legal meaning and approval

Notices with legal effect use tenant-owned wording approved by the tenant's legal team and reviewed by Nomology legal; dates, deadlines and amounts are inserted from the rules engine and calendars package, never typed into templates.

<!-- check:tenancy -->
### Tenant-editable content safety

Tenants may edit the wording of tenant-owned notices and the tenant name and help links in footers; they cannot remove the "why you received this" footer, privacy link or opt-out line for optional channels. Tenant edits are versioned, previewed and audited, and are checked against channel length limits and registered DLT templates.

<!-- check:disclosure -->
### Confidentiality and privacy in copy

Lock-screen-safe rule: SMS, WhatsApp and push contain only tenant short name, generic event, case reference, date and link; no party names, amounts, outcomes or document titles. Email subjects carry the reference, not party names. Templates use typed variables bound to the recipient's case at render time, and a missing variable fails the send rather than rendering blank or another case's value.

<!-- check:provenance -->
### Version and proof of what was shown

Each sent message is stored as rendered, with template ID and version, locale, DLT template ID (India SMS) and provider message ID, linked to the case and to the service-of-notice record.

<!-- check:localisation -->
### Translation quality and process

ICU templates with stable IDs, translator notes with channel limits, recipient language with fallbacks, separately registered DLT templates per language, and the authoritative language recorded for legal notices.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "retrieved": "2026-10-28",
    "title": "ICU User Guide: Formatting Messages",
    "url": "https://unicode-org.github.io/icu/userguide/format_parse/messages/",
    "vendor": "Unicode Consortium"
  }
]
```

<!-- end -->
