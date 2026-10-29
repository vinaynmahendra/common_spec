---
id: "DOC-tenant-facing-help-centre"
title: "Tenant-facing help centre"
parent: "DOC"
order: 4
type: "capability"
template: "ui"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "1fc8ed8bc6770613"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 17.4 Tenant-facing help centre

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:persona -->
## Persona and goal

**Goal: a person using the platform finds an answer to "how do I…" or "what does this mean" without leaving their task or contacting the secretariat.**

| Persona | Typical situation |
|---|---|
| Party without a lawyer (SEBI ODR investor, MSME claimant, consumer in a CORD tenant) | On a phone, unsure what a notice means or how to reply before a deadline; may be anxious |
| Counsel | Knows procedure, needs platform how-tos (bulk upload, bundle references, payment) |
| Secretariat / tribunal secretary | Needs exact steps for bulk actions, scheduling and deadline overrides |
| Neutral | Needs help with drafting tools, procedural orders, AI-assisted panels |
| Tenant admin | Configuring users, branding, rules, reports |

One help centre per tenant presentation (branding and terminology), built from one shared content base.

<!-- section:journey -->
## Journey steps

1. **Entry**: the user selects "Help" from the same place on every screen (header, consistent per WCAG 3.2.6), or a contextual "?" link next to a field or step, or arrives from a link in a notification or email.
2. **Contextual panel**: help opens in a side panel (desktop) or full-screen sheet (mobile) showing articles linked to the current route and step, without losing form state.
3. **Search**: the user searches; results are filtered to their persona and tenant.
4. **Article**: the user reads an article with steps, screenshots (synthetic data) and glossary explanations.
5. **Resolution or escalation**: "Did this help?" (yes/no). If no, options to contact the tenant's support (contact details from tenant settings) or, for parties, the secretariat of their case.
6. **Exit**: the user returns to the exact place in their task.

<!-- section:screens -->
## Screens

| Screen | Purpose | Key content | Actions |
|---|---|---|---|
| Help home (`/help`) | Browse by persona and topic | Top tasks for the user's persona, search box, contact options | Search, open topic, contact support |
| Contextual help panel | Help for the current step | 1–5 linked articles, glossary terms on this screen | Open article, close, open in full page |
| Search results (`/help/search?q=`) | Find articles | Results with title and one-line summary, persona badge | Open result, refine by topic |
| Article (`/help/articles/[slug]`) | Explain one task or concept | Steps, notes on deadlines (from tenant rules), related articles, last-updated date | Feedback, print, copy link, contact support |
| Glossary (`/help/glossary`) | Plain explanations of terms | Term, plain explanation, tenant variant | Search |
| Contact support | Route a question | Tenant support channels and hours; case secretariat contact for parties | Send message (creates a support ticket in the tenant's region) |

Route group: help is available inside every authenticated route group and in `(public)` for pre-sign-in topics (sign-in problems, invitation acceptance). Design links: to be added when Figma files exist.

<!-- section:states -->
## States per screen

| Screen | Loading | Empty | Error | Partial | Permission denied | Success |
|---|---|---|---|---|---|---|
| Help home | Skeleton list | n/a (always has top tasks) | "Help is not loading right now. You can still contact support: {supportContact}." | Tenant-specific articles missing: show platform articles | n/a | Top tasks shown |
| Contextual panel | Spinner with "Loading help for this step" (announced politely) | "There is no help article for this step yet. Search help or contact support." | As above | Some linked articles unavailable in the user's language: show available ones with a language note | n/a | Articles listed |
| Search | "Searching…" | "No articles match '{query}'. Try fewer words, or contact support." | "Search is not working right now. Browse topics instead." | n/a | n/a | Results with count announced ("7 articles found") |
| Article | Skeleton | n/a | "This article could not be loaded." | "This article is not yet available in {language}. Showing English." | Article for another persona: "This article is for {persona} users." with link to help home | Article shown |
| Contact support | Button disabled with "Sending…" | n/a | "Your message was not sent. Check your connection and try again." Message text kept | n/a | n/a | "Your message was sent. Reference {ticketRef}. {Tenant} usually replies within {responseTime}." |

<!-- section:validation -->
## Validation and business rules

- Articles referencing deadlines or fees insert values from tenant rules ([[PKG-rules-and-decision-engine]]) and calendars ([[PKG-calendars-and-deadline]]); no numbers are typed into articles.
- Articles are tagged by persona, route, tenant type and product (CORD, TERES); a party sees only party articles plus general ones.
- Tenant overrides: tenants may add articles and override wording of platform articles, except locked articles (security, privacy notice links, accessibility statement, platform terms). Overrides are versioned and previewed before publishing ([[PKG-tenant-terminology-and-copy]]).
- Contact form: message length 5–2,000 characters; no attachments in phase 1 (avoids uploads outside the case record); the case ID is attached automatically if opened from a case.

<!-- section:content -->
## Content and copy

Copy follows the voice guide ([[APP-voice-tone-and-content-style]]) and, for party-facing articles, [[DOC-plain-language-guidance-for]]. Terminology follows [[I18N-platform-glossary-and]] with tenant variants applied. Articles never give legal advice; they explain how the platform works and point to the tenant's rules for procedure. Articles describing legal effect (service, deemed receipt, deadlines) are approved by Nomology legal and, where institution rules define the effect, by the tenant.

<!-- section:accessibility -->
## Accessibility

- 3.2.6 Consistent Help: the Help entry point is in the same relative place on every page.
- 2.4.11 Focus Not Obscured: the side panel must not cover the focused form field; focus moves into the panel on open and returns to the trigger on close.
- 4.1.3 Status Messages: search result counts and "message sent" are announced through a live region.
- 1.4.10 Reflow: articles reflow at 320 CSS pixels; screenshots have text alternatives that describe the step, not the image.
- 3.1.2 Language of Parts: fallback-language articles carry the correct `lang`.
- Videos, if used, have captions and transcripts.

<!-- section:responsive -->
## Devices and responsiveness

Mobile first: the contextual panel becomes a full-screen sheet with a clear "Back to your form" button; articles are single-column. Supported: last two versions of Chrome, Safari, Firefox and Edge; Android and iOS browsers on low-end devices on 3G-class connections (article pages under 150 KB of JavaScript, proposed).

<!-- section:analytics -->
## Analytics events

Events (no personal data, no free text, no case content): `help_opened` {routeTemplate, persona, entry: header|contextual|notification}, `help_search` {resultCount, persona} (query text not stored), `help_article_viewed` {articleId, locale, fallback: bool}, `help_feedback` {articleId, helpful: bool}, `help_contact_sent` {persona}. Stored in the tenant's region; used to find missing or failing articles.

<!-- section:questions -->
## Open questions

- [ ] Content source: MDX in the repo (versioned with code) or a headless CMS (editable by product and tenant admins without deploys)?
- [ ] Is the contact form in scope for phase 1, or do tenants use their own support channels?
- [ ] Which languages are required at launch for each tenant? (See [[I18N-l10n]].)
- [ ] Should search be served by the platform search package ([[PKG-search]]) or a static index per locale?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenancy and branding

Help is rendered under the tenant resolved by [[MT-tenant-resolution]], with tenant branding, terminology variants and tenant-added articles; tenant overrides are cached with tenant ID in the key, and locked articles cannot be overridden. A user in two tenants sees the help of the active tenant, which is always visible in the header ([[PKG-tenant-and-role-switcher]]).

<!-- check:security -->
### Access and data exposure

Help content is non-confidential, but the contact form is authenticated, rate-limited and creates tickets only in the tenant's region; tenant-authored article content is sanitised (no scripts, links checked).

<!-- check:accessibility -->
### Accessibility (WCAG 2.2 AA)

Specific criteria listed in the Accessibility section (3.2.6, 2.4.11, 4.1.3, 1.4.10, 3.1.2); tested with the journey suite in [[TST-accessibility-testing]].

<!-- check:i18n -->
### Localisation

Articles are translated per locale through the workflow in [[I18N-i18n]]; missing translations fall back to English with a visible note and correct `lang`; deadlines in articles are inserted with time zone from tenant data.

<!-- check:observability -->
### Analytics and privacy

Events in the Analytics section carry no personal data or query text, stay in the tenant's region, and are deleted with tenant offboarding.

<!-- end -->
