---
id: "SEC-privacy-notice-copy"
title: "Privacy notice copy"
parent: "SEC-privacy-controls"
order: 3
type: "feature"
template: "content"
status: "draft"
owner: null
indicative: false
summary: "DPDP itemised notice, GDPR Art. 13/14 and PDPA notice text per journey, language availability, data fiduciary ownership"
links: []
rev: 2
syncHash: "54425eea58d59b58"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 13.2.3 Privacy notice copy

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> DPDP itemised notice, GDPR Art. 13/14 and PDPA notice text per journey, language availability, data fiduciary ownership

<!-- section:scope -->
## Scope and audiences

Governs the words of every privacy notice and privacy-related message on the platform:

- Short (layered) notices shown before data is collected in each journey: party registration (CORD, SEBI ODR), invitation acceptance (counsel, neutrals, staff), public filing entry, KYC step, hearing join (recording notice), WhatsApp / SMS opt-in, AI feature disclosure.
- Full privacy notices per fiduciary: one template for tenant institutions (configured with the tenant's details, where the tenant is fiduciary) and one for Nomology as fiduciary (CORD, website, billing contacts).
- First-contact notices in service emails and SMS to respondents.
- Rights request pages and responses ([[SEC-data-principal-rights-requests]]).
- Cookie banner and cookie notice on public pages.

Readers: parties without lawyers (SEBI ODR investors, MSME claimants), often reading on a phone, sometimes in a second language and under stress; counsel and neutrals (legally literate, time-poor); tenant staff.

<!-- section:voice -->
## Voice and tone

- **Plain and direct**: say what we collect, why, who sees it and what the reader can do. No "we may" where we do.
- **Neutral**: the notice must not suggest that sharing more data helps a party's case, or that refusing will harm it, unless that is a factual procedural consequence stated by the institution's rules.
- **Honest about limits**: where the case record cannot be erased, say so and say why.
- **Calm for stressful moments**: first-contact notices to respondents are factual and short; the case notice itself explains the dispute, the privacy notice only explains data use.

<!-- section:terminology -->
## Terminology and glossary alignment

| Canonical term | Use for | Avoid |
|---|---|---|
| personal data | All jurisdictions in UI copy | "PII", "personal information" (except where a law's own term is quoted) |
| the institution | The tenant as fiduciary / controller in tenant-facing copy, replaced by the tenant's display name | "the client", "the customer" |
| Nomology | Nomology Technology Private Limited (or TAPL / US entity as applicable) when it is the fiduciary or processor | "the platform owner" |
| your case record | The filed documents, orders and events of a case | "your file" |
| withdraw consent | Turning off a consent-based purpose | "opt out" (except for marketing) |
| Grievance Officer | DPDP contact; "Data Protection Officer" where GDPR / PDPA require | — |

Legal-term variants per jurisdiction: "data principal" (DPDP), "data subject" (GDPR) and "individual" (PDPA) appear only in the full notice's legal section, never in short notices. Terms are aligned with [[I18N-platform-glossary-and]].

<!-- section:patterns -->
## Microcopy patterns

| Pattern | Rule | Good | Bad |
|---|---|---|---|
| Short notice heading | States the action and the owner | "How {institution} uses your details for this claim" | "Privacy Policy" |
| Itemised list | One line per data item with its purpose (DPDP itemised notice) | "Your mobile number — to send you hearing dates and orders" | "Contact details for communication purposes" |
| Consent checkbox | Unticked; one purpose per box; states the purpose | "Send me case updates on WhatsApp" | "I agree to the terms and privacy policy" (bundled) |
| Withdraw link | Always next to consent and in settings | "You can turn this off at any time in Settings → Privacy" | — |
| Link to full notice | Descriptive | "Read the full privacy notice" | "Click here" |
| Dates | Absolute dates in the user's locale | "Last updated 14 March 2027" | "Updated recently" |

<!-- section:errors -->
## Error messages

| Code | Situation | Copy |
|---|---|---|
| PRIV-001 | Consent not given for a required purpose (registration) | "To file a claim here, we need to use your details as described above. If you do not want this, you can contact {institution} about other ways to file." |
| PRIV-002 | Identity check failed on a rights request | "We could not confirm it is you. Check the code we sent to {masked phone} and try again, or contact the Grievance Officer at {contact}." |
| PRIV-003 | Request is for another institution's data | "This request covers your details held by {institution}. If you also have a case with another institution, please send them a separate request." |
| PRIV-004 | Erasure refused for case record | "We have not deleted {items} because they form part of the record of your case, which {institution} must keep under {basis}. We have limited their use to what that requires." |

Errors never reveal whether another person has an account or a case.

<!-- section:legal -->
## Legal and declaration text

| Text | Owner | Approver | Versioned in | Record of what the user saw |
|---|---|---|---|---|
| Full notice — tenant as fiduciary (template) | Nomology legal (template) | Tenant's legal / privacy contact (filled version) | [[I18N-legal-declaration-and-consent]] | Version id on consent records and audit trail |
| Full notice — Nomology as fiduciary (CORD, website, billing) | Nomology legal | DPO | Same | Same |
| Short notices per journey | Product content designer | DPO; tenant where tenant is fiduciary | Same | Version id stored with the action (registration, invitation acceptance, hearing join) |
| Consent statements (each checkbox) | Product content designer | DPO | Same | `consent_record.notice_version_id` ([[SEC-consent-and-notice-management]]) |
| Recording notice for hearings | Tenant (based on its rules) with Nomology default | Tenant | Same | Attendance record stores notice version |
| Cookie notice | Nomology legal | DPO | Same | Consent cookie stores version |

Required content of a DPDP notice (to be verified against Rule 3 by legal) [R1]: itemised description of personal data and the specified purpose for each; the specific goods, services or uses enabled; a link or means to withdraw consent, to exercise rights and to complain to the Data Protection Board. GDPR Art. 13 / 14 content [R2] is covered by the full notice's legal section (controller identity, DPO contact, purposes and bases, recipients, transfers, retention, rights, complaint, source of data for Art. 14).

<!-- section:notifications -->
## Notifications and generated documents

- First-contact email to a respondent: one paragraph "Why you are receiving this and how your details are used", plus a link to the full notice. Subject lines never state the claim amount or the nature of the dispute.
- SMS (India, DLT-registered templates via [[PKG-notification-copy]]): "{institution}: details of how your data is used for case {ref}: {short link}". Max 160 characters including the link.
- WhatsApp opt-in confirmation: states the purpose and how to stop ("Reply STOP to turn off WhatsApp updates").
- Rights request responses are generated PDFs plus an email; the PDF uses the formal document theme ([[PKG-print-and-formal-document-theme]]).

<!-- section:plain -->
## Plain language for non-lawyer parties

- Reading level: short notices at about age 12 reading level (proposed; measured with a readability check for English and reviewed by a native speaker for other languages).
- Sentences under 20 words; one idea per sentence; active voice.
- Legal terms introduced with a plain explanation the first time ("the institution — {name}, which runs your case — decides how your data is used").
- Precision stays where it matters: who the fiduciary is, what cannot be erased, how to complain.

<!-- section:localisation -->
## Localisation readiness

- Strings in ICU MessageFormat with stable ids (`privacy.short.registration.items.mobile`), translator notes stating the legal effect.
- Notices available in every language the tenant enables; DPDP allows English or any Eighth Schedule language, and the reader should be able to choose (s.5(3)) [R1].
- Authoritative version: English, unless the tenant's legal team approves another language as authoritative for its jurisdiction. Translations of legal text are reviewed by a qualified legal translator before publication.

<!-- section:accessibility -->
## Accessible content

Notices are real text (not images or PDFs only), with headings, lists and descriptive links; consent controls are labelled checkboxes reachable by keyboard; language is marked with `lang`; WCAG 2.2 AA applies ([[APP-accessibility-wcag-2-1-aa]]).

<!-- section:governance -->
## Content governance and workflow

Copy lives in the legal text register; changes are pull requests to the content repository with DPO approval recorded; tenant-specific values (institution name, Grievance Officer contact, retention periods) are tenant settings validated for completeness before a notice can be published. Material changes trigger re-acceptance ([[SEC-consent-and-notice-management]]). Copy ships as content without a code deploy once approved.

<!-- section:questions -->
## Open questions

- [ ] Legal to confirm the exact DPDP Rule 3 notice elements and whether a consent-manager reference is required.
- [ ] Which languages are required at launch for SEBI ODR and CORD tenants?
- [ ] Does each institution want its own full notice (tenant-authored) or our template with its details?
- [ ] Who in Nomology is named as Grievance Officer / DPO in the Nomology-as-fiduciary notice?

<!-- checks -->
## Template checks

<!-- check:legal-accuracy -->
### Legal meaning and approval

Every notice element is traced to its legal source (DPDP s.5 and Rule 3, GDPR Arts 13–14, PDPA s.20) and approved by the DPO; tenant-filled notices are approved by the tenant's legal contact. Unconfirmed elements are flagged as open questions, not written as fact.

<!-- check:tenancy -->
### Tenant-editable content safety

Tenants can fill named slots (institution name, contacts, retention, languages) and add a tenant-specific section; they cannot remove the itemised list, the withdrawal and complaint sections, or insert markup (plain text with a small Markdown subset, sanitised). Values are per-tenant settings and cannot leak into another tenant's notice.

<!-- check:disclosure -->
### Confidentiality and privacy in copy

First-contact messages carry no claim details beyond the case reference; error messages never confirm another person's account or case.

<!-- check:provenance -->
### Version and proof of what was shown

The notice version id and language are stored with every consent record and with each action that relied on a notice (registration, invitation acceptance, hearing join), with rendered snapshots of each version kept.

<!-- check:localisation -->
### Translation quality and process

Translations by qualified legal translators, versioned with the source, published only when all enabled languages are complete; English authoritative unless the tenant designates otherwise.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Sections 5–6 (notice and consent), 8 (obligations of data fiduciary, including breach intimation), 11–14 (rights of data principal), 17 (exemptions).",
    "id": "R1",
    "issuer": "Government of India (MeitY)",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
  },
  {
    "excerpt": "Art. 12(3) one month to respond to requests (extendable by two months); Arts 13–14 information; Arts 15–22 rights; Art. 28 processors; Art. 30 records; Art. 32 security; Art. 33 notify the supervisory authority within 72 hours; Art. 34 communicate to data subjects; Chapter V transfers.",
    "id": "R2",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU / EEA",
    "kind": "regulation",
    "ref": "Regulation (EU) 2016/679",
    "title": "General Data Protection Regulation",
    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng"
  }
]
```

<!-- end -->
