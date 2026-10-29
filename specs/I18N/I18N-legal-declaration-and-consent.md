---
id: "I18N-legal-declaration-and-consent"
title: "Legal, declaration and consent text register"
parent: "I18N-content"
order: 1
type: "feature"
template: "content"
status: "draft"
owner: null
indicative: false
summary: "Every text with legal effect: owner, approver, tenant configurability, version recording and re-acceptance rules"
links: []
rev: 2
syncHash: "c5ccbca71e108712"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 4.3.1 Legal, declaration and consent text register

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Every text with legal effect: owner, approver, tenant configurability, version recording and re-acceptance rules

<!-- section:scope -->
## Scope and audiences

The register of every piece of text on the platform that has legal effect or records a person's agreement: terms, privacy notices, consents, declarations made when filing or accepting an appointment, statements about service and receipt, recording and confidentiality undertakings, e-signature statements and AI-use disclosures. It covers screens, emails, PDFs and API portal texts, in every locale. Readers range from unrepresented parties to counsel and neutrals. For each text it records owner, approver, tenant configurability, versioning and re-acceptance rules, and how the version a user saw is recorded. The wording of each text is written and approved by its owner; this node does not invent legal content.

<!-- section:voice -->
## Voice and tone

Legal texts are precise first and plain second: where a text must use legal wording, it is shown together with a plain explanation ([[DOC-plain-language-guidance-for]]) and the screen states which governs. No text may suggest the platform favours a party or gives legal advice.

<!-- section:terminology -->
## Terminology and glossary alignment

Texts use glossary terms ([[I18N-platform-glossary-and]]). Where an institution's rules use their own defined terms (for example their own term for the tribunal or for a filing), tenant-owned texts use those defined terms and the glossary records them as the tenant variant.

<!-- section:patterns -->
## Microcopy patterns

- **Acceptance control**: an unticked checkbox with the full statement as its label, or a button whose label states the act ("I agree and file") when the institution's rules treat filing itself as the declaration. Never a pre-ticked box.
- **Show before act**: the full text (or a link that opens it in the same flow) is shown before the user can act; scrolling to the end is not required, but the text must be reachable by keyboard and screen reader.
- **Version label**: every legal text shows its version and effective date in small print ("Version 3, effective 1 Dec 2026").
- **Receipt**: after acceptance, the receipt and confirmation email state which texts were accepted, with versions.

<!-- section:errors -->
## Error messages

| Code | Final copy |
|---|---|
| `legal.acceptance.required` | "To continue, confirm that you agree to the statement above." |
| `legal.version.changed` | "The text you were reading has been updated. Read the new version before you continue." |
| `legal.locale.unavailable` | "This text is not available in {language}. It is shown in English, which is the authoritative version." |

<!-- section:legal -->
## Legal and declaration text

**Register** (owner = who writes and is responsible; approver = who signs off each version)

| Key | Text | Owner | Approver | Tenant configurable | Re-acceptance |
|---|---|---|---|---|---|
| `platform.terms` | Platform terms of use | Nomology legal (contracting entity per region: NTPL, TAPL or US entity) | Nomology legal | No | On material change, at next sign-in |
| `privacy.notice.<journey>` | Privacy notices per journey (DPDP, GDPR Art. 13/14, PDPA) | Data fiduciary / controller for the processing (tenant, Nomology or both, per [[SEC-privacy-notice-copy]]) | Nomology legal + tenant | Partly (tenant identity and contacts) | Notice of change; consent re-sought where consent is the basis |
| `consent.electronic-service` | Consent to electronic communication and service | Tenant (institution rules) | Tenant legal | Yes | On material change, before next service |
| `consent.whatsapp`, `consent.sms` | Opt-in to WhatsApp / SMS | Nomology legal | Nomology legal | Sender identity only | On change of purpose |
| `declaration.statement-of-truth` | Declaration on filing a claim or reply | Tenant (rules) | Tenant legal | Yes | Per filing (always shown) |
| `declaration.neutral-independence` | Neutral's declaration of acceptance, availability, impartiality and independence | Tenant (rules) | Tenant legal | Yes | Per appointment |
| `undertaking.hearing-confidentiality` | Participant confidentiality and no-recording undertaking | Tenant | Tenant legal | Yes | Per hearing |
| `consent.hearing-recording` | Notice and consent for recording and transcription | Tenant, with Nomology legal for platform processing | Tenant legal + Nomology legal | Yes | Per hearing |
| `undertaking.transcriber-confidentiality` | Transcriber confidentiality undertaking | Nomology legal (for platform-engaged transcribers) or tenant | Respective legal | Yes | Yearly and on change |
| `disclosure.ai-use` | Disclosure that AI assisted with a summary or draft, where the tenant has enabled AI | Tenant + Nomology legal ([[AI-ai-governance-and-impact]]) | Both | Yes | On change |
| `statement.e-signature` | Statement shown when signing electronically | Nomology legal + e-sign provider terms ([[INT-e-signature]]) | Nomology legal | No | Per signature |
| `statement.service-receipt` | Wording of service and delivery receipts | Tenant (rules) | Tenant legal | Yes | n/a (generated per notice) |
| `consent.kyc` | Notice and consent for identity verification and screening | Nomology legal + tenant | Both | Partly | Per verification |
| `payment.terms` | Fee, refund and payment terms | Tenant (fee schedule) / billing entity | Tenant + Nomology finance and legal | Yes | Per payment |
| `api.terms` | API terms of use | Nomology legal | Nomology legal | No | Per API client on change |

**Recording**: every display of an acceptance control and every acceptance writes to `legal_acceptances` (tenant-owned, forced RLS): `tenant_id`, `user_id`, `on_behalf_of_party_id`, `text_key`, `text_version`, `locale`, `authoritative_locale`, `content_hash` of the rendered text including tenant overrides, `context` (case, filing, hearing IDs), `accepted_at` (server time), `channel` (web, API), `request_id`. Rendered text versions are immutable in `legal_text_versions` and retrievable by hash through [[I18N-content]]. Acceptance events also go to the audit trail ([[PKG-audit-trail]]) and are retained for the case retention period ([[PKG-retention-and-deletion-schedule]]).

Under the DPDP Act, notices and consent requests must be available in English or a language of the Eighth Schedule to the Constitution at the person's option [R1]; GDPR requires clear and plain language [R2]. Which texts need which locales per tenant is a legal decision recorded per text.

<!-- section:notifications -->
## Notifications and generated documents

Confirmation emails list accepted texts with version numbers and link to the stored text; they never paste the full declaration text into SMS or WhatsApp. Emails are stored as sent ([[PKG-notifications]]).

<!-- section:localisation -->
## Localisation readiness

Each text version has an authoritative locale (usually English, unless the tenant's rules say otherwise) and translations marked as such. Translations of legal texts are made by legal translators and approved by the text's approver; untranslated texts show the authoritative version with a notice (`legal.locale.unavailable`).

<!-- section:governance -->
## Content governance and workflow

Texts are drafted by their owner, reviewed by content design for clarity, approved by the approver in the admin workflow, and published as a new immutable version with an effective date. Tenant-owned texts are edited in the tenant admin console with a preview; platform-owned texts change through a pull request plus legal approval recorded on the version. Locked message IDs cannot be overridden through language packs.

<!-- section:questions -->
## Open questions

- [ ] Legal to confirm the owner and approver for each row, per region and contracting entity.
- [ ] Which texts need re-acceptance on change, and what counts as a material change?
- [ ] Is the authoritative language always English, or may a tenant's rules make another language authoritative?
- [ ] Is click-acceptance sufficient for declarations under each institution's rules, or is e-signature required for some (for example the neutral's declaration)?

<!-- checks -->
## Template checks

<!-- check:legal-accuracy -->
### Legal meaning and approval

Every text has a named owner and approver class; tenant-owned texts follow institution rules; this register does not write legal wording itself.

<!-- check:tenancy -->
### Tenant-editable content safety

Tenant-configurable texts are marked per row; platform terms, API terms and e-signature statements are locked; overrides are versioned, previewed and RLS-protected.

<!-- check:disclosure -->
### Confidentiality and privacy in copy

SMS and WhatsApp never carry declaration text or case detail; confirmation emails list text names and versions only.

<!-- check:provenance -->
### Version and proof of what was shown

Every acceptance stores text key, version, locale, authoritative locale, content hash of the rendered text including overrides, context IDs and server timestamp; text versions are immutable and retrievable by hash; confirmations are stored as sent; audit events are tamper-evident.

<!-- check:localisation -->
### Translation quality and process

Authoritative locale per version, legal translators only, and a visible notice when the authoritative text is shown instead of a translation; India notices follow the DPDP language option.

<!-- citations -->
## Citations

```json
[
  {
    "clause": "Section 5(3)",
    "excerpt": "The Data Fiduciary shall give the Data Principal the option to access the notice and consent request in English or any language specified in the Eighth Schedule to the Constitution.",
    "id": "R1",
    "issuer": "Government of India (MeitY)",
    "jurisdiction": "India",
    "kind": "regulation",
    "ref": "Act No. 22 of 2023",
    "title": "Digital Personal Data Protection Act, 2023",
    "url": "https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf"
  },
  {
    "clause": "Article 12(1)",
    "excerpt": "Information to data subjects must be provided in a concise, transparent, intelligible and easily accessible form, using clear and plain language.",
    "id": "R2",
    "issuer": "European Parliament and Council",
    "jurisdiction": "EU",
    "kind": "regulation",
    "ref": "Regulation (EU) 2016/679",
    "title": "General Data Protection Regulation",
    "url": "https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng"
  }
]
```

<!-- end -->
