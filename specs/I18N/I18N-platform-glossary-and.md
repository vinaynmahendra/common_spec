---
id: "I18N-platform-glossary-and"
title: "Platform glossary and terminology governance"
parent: "I18N"
order: 4
type: "capability"
template: "content"
status: "draft"
owner: null
indicative: false
summary: "Canonical terms keyed to domain IDs, permitted tenant / procedure variants, banned synonyms, glossary in translation memory"
links: []
rev: 2
syncHash: "f9340aa535879924"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 4.4 Platform glossary and terminology governance

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Canonical terms keyed to domain IDs, permitted tenant / procedure variants, banned synonyms, glossary in translation memory

<!-- section:scope -->
## Scope and audiences

The canonical list of terms used across UI, notifications, generated documents, API, help centre, AI prompts and translations, each keyed to a domain concept ID, with permitted tenant and procedure variants and banned synonyms. It is loaded into the translation management system's termbase and into lint rules. Readers: content designers, engineers, translators, prompt authors and tenant admins configuring terminology.

<!-- section:voice -->
## Voice and tone

Glossary definitions are short, neutral and plain: one sentence a party could understand, plus a precise note for staff where needed. Definitions never characterise a party's position.

<!-- section:terminology -->
## Terminology and glossary alignment

| Concept ID | Canonical term | Plain definition | Permitted variants (who may use) | Banned |
|---|---|---|---|---|
| `term.case` | case | A dispute being handled on the platform. | matter, dispute (tenant display setting) | lawsuit, ticket, complaint (except as SEBI ODR tenant variant if its rules use it) |
| `term.claimant` | claimant | The person or business that started the case. | complainant, applicant (tenant rules) | plaintiff, petitioner |
| `term.respondent` | respondent | The person or business the case is against. | opposite party (tenant rules) | defendant, accused |
| `term.party` | party | A claimant or respondent in a case. | none | client, litigant, user (meaning a party) |
| `term.representative` | representative | A lawyer or other person acting for a party. | counsel (UI), advocate (India tenant variant) | attorney (except US tenant variant) |
| `term.neutral` | neutral | An independent person who helps resolve the case. Used in staff and API contexts; parties see the role name. | arbitrator, mediator, conciliator (by `neutralRole`) | judge, adjudicator |
| `term.tribunal` | tribunal | The arbitrator or arbitrators appointed to a case. | arbitral tribunal | court, bench |
| `term.secretariat` | secretariat | The institution staff who manage cases. | registry, case manager (tenant variant) | admin (for this role) |
| `term.tribunal-secretary` | tribunal secretary | A person who assists the tribunal with administration. | none | clerk |
| `term.filing` | filing | Documents a party sends to the case at one time. | submission (tenant rules) | upload (as a noun) |
| `term.document` | document | One file in the case record, with its versions. | exhibit (for evidence documents) | attachment (in case contexts) |
| `term.bundle` | bundle | An ordered, paginated set of documents for a hearing. | hearing bundle, eBundle | binder, pack |
| `term.hearing` | hearing | A session where the tribunal hears the parties, online or in person. | session (mediation) | trial, meeting (for hearings) |
| `term.procedural-order` | procedural order | A written direction from the tribunal about how the case will run. | direction (tenant rules) | ruling |
| `term.award` | award | The arbitrator's written decision. | final award, partial award | judgment, verdict, decree |
| `term.settlement-agreement` | settlement agreement | A written agreement between the parties that resolves the dispute. | none | deal |
| `term.notice` | notice | An official message about the case. | none | alert, letter |
| `term.service` | service | Formally delivering a notice or document to a party. | none | sending (for formal service) |
| `term.deadline` | deadline | The last date and time to do something in the case. | due date (with time and zone) | ETA |
| `term.transcript` | transcript | A written record of what was said in a hearing. | none | minutes |
| `term.tenant` | (internal only) tenant | An institution or organisation using the platform. Never shown to parties; users see the institution's name. | institution, organisation (UI) | customer, account (in UI) |

Procedure variants: SEBI ODR institution tenants and arbitral institutions may have defined terms in their rules; each tenant's variants are recorded here after legal confirms them against the tenant's rules.

<!-- section:patterns -->
## Microcopy patterns

- A glossary term is written the same way everywhere (lower case except at sentence start; no capitalised "Case" in running text).
- On first use in party-facing screens, the term links to its plain definition (help glossary).
- Tenant variants apply everywhere the term appears for that tenant: screens, emails, PDFs, search labels, exports and help ([[PKG-tenant-terminology-and-copy]]).

<!-- section:errors -->
## Error messages

Terminology lint errors (developer-facing, final copy):
- `glossary.banned-term`: "'{found}' is a banned synonym for '{canonical}' ({conceptId}). Use the canonical term or the tenant variant."
- `glossary.unknown-variant`: "'{variant}' is not a permitted variant of {conceptId} for this tenant. Add it to the glossary or use '{canonical}'."

<!-- section:legal -->
## Legal and declaration text

Glossary definitions are not legal definitions; legal definitions come from the institution's rules or statute and are cited where shown. Variants that mirror defined terms in a tenant's rules are approved by that tenant's legal team; platform definitions are approved by Nomology legal. See [[I18N-legal-declaration-and-consent]] for texts with legal effect.

<!-- section:localisation -->
## Localisation readiness

The glossary is exported as a TBX termbase into the translation management system for each launch locale; each locale entry has the approved term, plain definition and notes. Translators must use termbase entries; deviations are flagged by the TMS quality check. AI prompts load the glossary for the tenant and locale ([[AI-prompt-management]]).

<!-- section:governance -->
## Content governance and workflow

Owner: content design, with Nomology legal for definitions of legal concepts. New terms or variants are proposed by pull request to `packages/i18n/glossary.yaml` (source of truth), reviewed by content design and, for legal concepts, legal. Tenant variants requested by a tenant are added after legal confirmation. Disputes between product, legal and tenant preferences are decided by the product lead with legal advice.

<!-- section:questions -->
## Open questions

- [ ] Confirm defined terms used by each launch tenant's rules (for example a SEBI ODR institution's own terms for the parties), with legal.
- [ ] Is "neutral" acceptable to parties anywhere, or staff and API only? Proposal: staff and API only.
- [ ] Which locales get the termbase first?

<!-- checks -->
## Template checks

<!-- check:legal-accuracy -->
### Legal meaning and approval

Glossary definitions are explicitly not legal definitions; tenant variants that mirror defined terms in institution rules are approved by that tenant's legal team.

<!-- check:terminology -->
### Terminology consistency

One canonical term per concept ID with plain definition, permitted variants and banned synonyms; enforced by lint on message catalogues, OpenAPI descriptions and help content, and by the TMS termbase for translations.

<!-- check:tenancy -->
### Tenant-editable content safety

Tenants choose only from permitted variants listed here; variants apply across all channels through tenant language packs; new variants need legal confirmation.

<!-- check:localisation -->
### Translation quality and process

TBX termbase per locale in the TMS; translators must use approved terms, with automated QA flags.

<!-- check:ai-content -->
### AI-generated and assisted text

Prompts load the tenant and locale glossary; evals check banned terms in outputs ([[TST-evals-and-ai-testing]]).

<!-- end -->
