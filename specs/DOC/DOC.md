---
id: "DOC"
title: "Documentation and Developer Experience"
parent: null
order: 17
type: "area"
template: "area"
childTemplate: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 3
syncHash: "4364fbc815c7ef14"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 17 Documentation and Developer Experience

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Documentation and Developer Experience makes the platform understandable to the people who build, run, integrate with and use it: engineers (architecture docs, runbooks, onboarding), integrators at tenants and aggregators (API reference, developer portal, API copy), and tenant users (help centre and plain-language guidance for unrepresented parties).

**In scope**: architecture overview, C4 diagrams and runbooks ([[DOC-architecture-docs-adrs-runbooks]]); public API and webhook documentation and the developer portal ([[DOC-api-documentation-openapi]]); developer-facing API wording ([[DOC-developer-facing-api-copy]]); engineer onboarding ([[DOC-onboarding-guide-for-engineers]]); tenant-facing help centre ([[DOC-tenant-facing-help-centre]]); plain-language guidance for unrepresented parties ([[DOC-plain-language-guidance-for]]).

**Out of scope**: the ADR process and decision records ([[FND-governance]], [[ADR]]); the API contracts themselves ([[INT-public-api-and-webhooks]] and its children); in-product microcopy and voice ([[APP-voice-tone-and-content-style]]); error message catalogue ([[APP-error-message-catalogue]]); tenant-facing release notes content process ([[DEP-release-notes-and-change]]).

<!-- section:goals -->
## Goals and non-goals

Proposed targets:
1. Docs live next to the code they describe and are updated in the same pull request; 100% of public API operations and webhook events have reference docs generated from the contract.
2. Every production alert links to a runbook; 0 alerts without a runbook at Phase 8 exit.
3. A new engineer opens a first reviewed pull request within 5 working days of joining.
4. An integrator can make a first authenticated sandbox API call within 30 minutes using only the developer portal.
5. Help centre articles exist for every persona journey and are reachable from the same place on every screen (WCAG 3.2.6 Consistent Help).
6. Plain-language party guidance is comprehension-tested with representative users before each launch locale goes live.

**Non-goals**: a separate documentation team writing engineering docs; documentation of tenants' institutional rules (tenants own those); legal advice to parties.

<!-- section:principles -->
## Principles

1. **Docs as code.** Engineering and API docs are Markdown/MDX in the repo, reviewed in pull requests and built in CI.
2. **Generate reference, write guidance.** Reference material (API, events, config, env variables) is generated from source; humans write concepts, tutorials and runbooks.
3. **One term per concept** from the platform glossary ([[I18N-platform-glossary-and]]) across docs, API and UI.
4. **No real tenant or case data** in any documentation, screenshot or example.
5. **Every page has an owner and a last-reviewed date**; pages older than 12 months unreviewed are flagged.
6. **Documentation meets WCAG 2.2 AA** like the product.

<!-- section:context -->
## Context and boundaries

| Audience | Docs | Where published |
|---|---|---|
| Engineers, coding assistants | Architecture, runbooks, onboarding, standards | Internal docs site built from `docs/` (SSO) |
| On-call and operations | Runbooks | Internal docs site, linked from alerts ([[OBS-alerting]]) |
| Integrators (tenants, aggregators such as NSE for SEBI ODR matters) | API reference, guides, changelog | Developer portal (`apps/developer-portal`) |
| Tenant admins, secretariat, neutrals, counsel | Help centre | Help centre, per tenant branding |
| Parties without lawyers | Plain-language guidance | In-product and help centre |

<!-- section:decisions -->
## Key decisions

- [[ADR-next-js-hosting]] — the developer portal and help centre are static or server-rendered Next.js apps hosted like the platform.
- Proposed ADRs: docs site generator (Next.js + MDX vs a dedicated docs framework), help centre content source (repo MDX vs headless CMS), diagram tooling (Structurizr DSL vs Mermaid).

<!-- section:map -->
## Capability map

| Child | Owns |
|---|---|
| [[DOC-architecture-docs-adrs-runbooks]] | arc42 overview, C4 diagrams, runbook standard and template |
| [[DOC-api-documentation-openapi]] | OpenAPI and AsyncAPI generation, linting, portal, changelog, sandbox |
| [[DOC-developer-facing-api-copy]] | Wording of API errors, descriptions and webhook docs |
| [[DOC-onboarding-guide-for-engineers]] | Day 1 to week 2 path for engineers |
| [[DOC-tenant-facing-help-centre]] | Help centre journeys, contextual help, search, tenant overrides |
| [[DOC-plain-language-guidance-for]] | Reading targets and journey copy for unrepresented parties |

<!-- section:phasing -->
## Phasing

| Phase ([[PLAN]]) | Lands |
|---|---|
| 0 | Docs folder, onboarding guide v1, architecture overview skeleton, runbook template |
| 3 | Help centre skeleton with first journeys; plain-language rules for the filing journey |
| 5 | Developer portal with public API reference, sandbox and changelog |
| 7 | Runbooks for every alert |
| 8 | Docs review cycle running; comprehension testing evidence for launch locales |

<!-- section:risks -->
## Risks and open questions

- [ ] Owner for the area to be named (proposed: engineering excellence lead for engineering docs; product lead for help centre).
- [ ] Help centre content source and translation workflow to be decided with [[I18N-i18n]].
- [ ] Risk: runbooks drift from infrastructure; mitigated by linking runbooks to alerts and testing them in game days.

<!-- checks -->
## Template checks

<!-- check:ownership -->
### Ownership and governance

Proposed: engineering excellence lead owns engineering and API docs; product leads (CORD, TERES) own the help centre and party guidance; content design and legal review legal-procedure wording.

<!-- check:boundaries -->
### Scope and boundaries

Microcopy and the error catalogue live in [[APP]]; this area covers documentation. The ADR process is in [[FND-governance]]. API contracts are in [[INT]]; this area documents them.

<!-- check:principles -->
### Principles and enforcement

Docs-as-code is enforced by CI (docs build, link check, Spectral lint on contracts); reference generation by the contract pipeline; glossary use by a terminology lint on docs and message catalogues; page owner and review date by front-matter required fields checked in CI.

<!-- check:compliance -->
### Regulatory and control mapping

Runbooks support ISO/IEC 27001:2022 documented operating procedures; help centre and party guidance support WCAG 2.2 AA and plain-language duties in privacy law (for example GDPR Article 12); API docs support client security questionnaires about integration security.

<!-- check:quality -->
### Quality targets

Targets listed in Goals (first API call in 30 minutes, first PR in 5 days, 0 alerts without runbook).

<!-- end -->
