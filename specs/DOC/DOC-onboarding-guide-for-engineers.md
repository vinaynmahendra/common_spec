---
id: "DOC-onboarding-guide-for-engineers"
title: "Onboarding guide for engineers"
parent: "DOC"
order: 3
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "ad629b710868fd52"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 17.3 Onboarding guide for engineers

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Defines the onboarding path for a new engineer (employee or contractor) from first day to first production change: access, local set-up, required reading, security and privacy training, and a guided first task. It also sets how the guide is kept working. It lives at `docs/onboarding/` and is the entry point to [[FND-monorepo]], [[FND-language-and-conventions]] and the rest of the standards.

<!-- section:rules -->
## Rules

- **ONB-1** Day 1 checklist: identity provider account, GitHub organisation membership with MFA, team membership for CODEOWNERS, engineering SSO for preview and non-prod environments, chat channels. No production access in the first 30 days; production access afterwards follows just-in-time rules ([[FND-environments]] ENVS-9).
- **ONB-2** Local set-up works on macOS, Linux and Windows (WSL2) with: install Node.js via the version in `.nvmrc`, `corepack enable`, `pnpm install`, `pnpm dev:up` (Docker Compose stack), `pnpm db:reset && pnpm seed`, `pnpm dev`. Target: running app with fixture tenants `arb-inst`, `odr-inst`, `cord` within 60 minutes.
- **ONB-3** Required reading in week 1, each with a short self-check: architecture overview ([[DOC-architecture-docs-adrs-runbooks]]); tenancy and isolation ([[MT-isolation-strategy]], [[ADR-tenant-isolation]]); data residency ([[MT-data-residency-2]]); workflow layering ([[WF-separation-of-concerns-temporal]]); standards in [[FND-governance]]; glossary ([[I18N-platform-glossary-and]]).
- **ONB-4** Training before the first merged PR: secure coding basics for our stack, personal data handling under DPDP, GDPR and PDPA, confidentiality of arbitration and ODR records, and accessibility basics. Completion is recorded for ISMS evidence.
- **ONB-5** First task: a `good-first-task` ticket that touches one package, adds a test, uses the PR template and goes through preview and staging. A buddy is assigned for the first two weeks.
- **ONB-6** The guide has an owner, and every new joiner records time-to-running-stack and any step that failed; the owner fixes failing steps within 5 working days.
- **ONB-7** The guide is also written for coding assistants: a root `AGENTS.md` / `CLAUDE.md` generated from the standards nodes, listing commands and the non-waivable rules.
- **ONB-8** Offboarding mirrors onboarding: access removed on the last day, GitHub membership and CODEOWNERS updated, any personal access tokens revoked.

<!-- section:rationale -->
## Rationale

- **ONB-1** The 30-day delay on production access limits the impact of mistakes while a person learns the tenancy model, and is easy to explain to auditors.
- **ONB-4** Engineers handle confidential case material indirectly (logs, support access); training before the first change sets expectations early.

<!-- section:tooling -->
## Tooling and configuration

`docs/onboarding/README.md`, `scripts/doctor.ts` (`pnpm doctor` checks Node, pnpm, Docker, ports and env), onboarding issue template in the ticketing system with the checklist, training records in the HR or ISMS system.

<!-- section:enforcement -->
## Enforcement

`pnpm doctor` gives actionable errors; onboarding ticket must be closed before production access is requested; training completion is checked before GitHub team membership with write access to `main`-protected repos is granted (manual step by the engineering manager, recorded).

<!-- section:examples -->
## Examples

Good: a new engineer reports "`pnpm dev:up` fails on Apple silicon because the Temporal image is amd64-only"; the owner pins a multi-arch image and updates the guide that week.

Bad: onboarding that depends on copying another engineer's `.env.local`.

<!-- section:exceptions -->
## Exceptions

Contractors with limited scope may get a reduced reading list approved by their engineering manager; training (ONB-4) is not reducible.

<!-- section:questions -->
## Open questions

- [ ] Training provider and record system for ONB-4.
- [ ] Is 30 days the right delay for production access, and who approves earlier access for senior hires?
- [ ] Do contractors from third-party firms use our laptops or their own (device management requirement)?

<!-- checks -->
## Template checks

<!-- check:onboarding -->
### Onboarding and usability

This node is the onboarding mechanism: a single command sequence, `pnpm doctor` diagnostics, recorded time-to-running-stack per joiner, and a generated assistant context file kept in sync with the standards.

<!-- check:compliance -->
### Compliance evidence

Supports ISO/IEC 27001:2022 people controls (awareness and training, terms of employment) and access provisioning and removal evidence (ONB-1, ONB-8).

<!-- check:measurement -->
### Adoption measurement

Time to running local stack (target under 60 minutes), time to first merged PR (target 5 working days), failed onboarding steps reported per quarter.

<!-- check:ownership -->
### Ownership and change

Owner: engineering excellence lead; each standard owner keeps their section of the reading list current.

<!-- end -->
