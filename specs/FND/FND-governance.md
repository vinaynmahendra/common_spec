---
id: "FND-governance"
title: "Governance"
parent: "FND"
order: 5
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: "Architecture Decision Records (ADRs), coding standards, PR templates, CODEOWNERS"
links: []
rev: 2
syncHash: "b8be001cd78e7aad"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 1.5 Governance

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Architecture Decision Records (ADRs), coding standards, PR templates, CODEOWNERS

<!-- section:purpose -->
## Purpose and scope

Sets how technical decisions are made and recorded, which coding standards apply, what every pull request must state, who must review which paths, and how the `main` branch is protected. It is the backbone of change management evidence for ISO 27001 and SOC 2. Release-level change management is in [[DEP-release-notes-and-change]]; architecture documentation in [[DOC-architecture-docs-adrs-runbooks]].

<!-- section:rules -->
## Rules

**Decision records**
- **GOV-1** A decision record (ADR node under [[ADR]]) is required before merging code that: adds a datastore, queue, cloud service or region; changes tenancy, residency or isolation; adds or replaces a library on the core list in [[APP-framework-dependencies]]; adds a third party that processes personal data; changes authentication or cryptography; or makes a breaking change to a public API or webhook contract.
- **GOV-2** Each ADR has status (`proposed`, `accepted`, `superseded`, `deprecated`), context, options considered, decision, consequences, and links to the nodes it shapes. Accepted ADRs are not edited; a new ADR supersedes them.
- **GOV-3** ADRs are approved by the CTO plus the owner of each affected area; security-relevant ADRs also need the information security owner.

**Standards index**
- **GOV-4** Coding standards are the standard nodes in this tree: [[FND-monorepo]], [[FND-language-and-conventions]], [[FND-environment-management]], [[APP-server-actions-and-mutation]], [[APP-client-state-and-data-fetching]], [[DEP-database-migration-strategy-zero]], [[TST-unit-integration-contract-and]], [[I18N-i18n]]. Rules are referenced by ID (for example CONV-5) in reviews and tool messages.

**Pull requests**
- **GOV-5** Every pull request uses `.github/pull_request_template.md`, links a ticket, and answers each item (`yes`, `no` or `n/a` with reason):
  - Tenant impact: new tenant-owned table? RLS policy and isolation test added ([[MT-lint-review-check-that-every]])?
  - Migration phase: none / expand / backfill / contract ([[DEP-database-migration-strategy-zero]])
  - Feature flag and default state ([[PKG-feature-flags]])
  - Personal data: new fields, logging, retention ([[PKG-data-retention-legal-hold-and]])
  - User-facing text: message IDs added, glossary terms used ([[I18N-platform-glossary-and]])
  - Accessibility checked for changed UI ([[TST-accessibility-testing]])
  - Audit events for legally significant actions ([[PKG-audit-trail]])
  - Docs, runbook or API changelog updated
  - Rollback: how to undo if this goes wrong
- **GOV-6** Pull requests are small (proposed guideline: under 400 changed lines excluding generated files); larger ones need a reason in the description.
- **GOV-7** `main` is protected by a GitHub ruleset: changes only through pull requests and the merge queue, squash merge, linear history, all required checks green, at least one approval, code owner approval, stale approvals dismissed on new commits, no force pushes or deletions. High-risk paths need two approvals.
- **GOV-8** Ruleset bypass is limited to the `release-admins` team and used only for emergency changes under [[DEP-release-notes-and-change]]; every bypass is reviewed within two business days.

**CODEOWNERS**
- **GOV-9** Every path has an owner team. Required paths:

| Path | Owners |
|---|---|
| `/packages/db/**`, `**/prisma/migrations/**` | `platform-data`, `security` |
| `/packages/auth/**`, `/packages/authz/**`, `/packages/security/**` | `security` |
| `/packages/audit/**`, `/packages/retention/**` | `platform-data`, `security` |
| `/packages/ai/**` | `ai-platform` |
| `/packages/i18n/**`, `/packages/content/**` | `frontend-platform`, `content` |
| `/.github/**`, `/turbo.json`, `/tooling/**`, `/pnpm-workspace.yaml` | `eng-excellence`, `devops` |
| `/apps/web/app/(platform-admin)/**` | `security`, `frontend-platform` |
| `/packages/domain-<name>/**` | owning domain team |

<!-- section:rationale -->
## Rationale

- **GOV-1** The triggers are the decisions that are hardest to reverse or that change audit scope; anything else is handled in normal review.
- **GOV-5** The checklist forces the questions that are specific to this platform (tenancy, residency, legal text, audit) at the moment the author knows the answers.
- **GOV-7** Squash merge plus conventional PR titles gives one commit per reviewed change, which makes the ticket → PR → deploy trail easy to sample.
- **GOV-9** Migrations and authorisation code are where a single mistake can expose one tenant's data to another; a second specialist reviewer is cheap insurance.

<!-- section:tooling -->
## Tooling and configuration

- GitHub rulesets on `main` and `release/*` tags [R1]; merge queue enabled.
- `.github/CODEOWNERS` [R2], validated by a CI job that checks every path has an owner and every team exists.
- `.github/pull_request_template.md`; a CI action that fails if mandatory checklist items are left blank.
- ADR nodes in the spec workspace (area 19), with an index in `docs/adr/README.md`.

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| GOV-1 | PR template question "ADR needed?"; CODEOWNERS for core-list `package.json` changes; reviewer checklist |
| GOV-2, GOV-3 | ADR node template fields; approval recorded on the ADR node |
| GOV-5 | PR checklist action (required check) |
| GOV-6 | Size label bot; advisory only |
| GOV-7 | Ruleset (required) |
| GOV-8 | Ruleset bypass list; monthly audit-log review by information security |
| GOV-9 | CODEOWNERS validation job (required) |

<!-- section:examples -->
## Examples

Good: adding OpenSearch for the Temporal visibility store opens ADR "Temporal visibility store" (proposed), links [[INF-temporal]] and [[WF-separation-of-concerns-temporal]], and the infra PR references it.

Bad: a PR that adds a new SMS provider for India with no ADR and no sub-processor update, approved by one domain engineer.

<!-- section:exceptions -->
## Exceptions

Exceptions to any standard are recorded in `tooling/dependency-rules/exceptions.yaml` (code-level) or as a proposed ADR (design-level), each with owner, reason, risk note, ticket and expiry. The exceptions list is reviewed monthly; security-relevant exceptions are copied to the risk register owned by [[SEC-isms-controls]]. Rules marked non-waivable in any standard cannot be excepted.

<!-- section:questions -->
## Open questions

- [ ] Is the spec workspace or the repository the source of truth for ADRs? Proposal: spec workspace, with the repo index generated from it.
- [ ] Confirm team names and membership for CODEOWNERS.
- [ ] Are two approvals required for all `prisma/migrations/**` changes or only contract-phase migrations?
- [ ] Should client-driven requirements (for example a client contract clause) be recorded as ADR context with the contract reference, given contract confidentiality?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Rulesets, CODEOWNERS validation and the PR checklist action are required checks; ADR approval is recorded on the node. The only review-only items are GOV-1 judgement ("does this need an ADR?") and GOV-6 size guidance. Bypass is limited and audited (GOV-8).

<!-- check:exceptions -->
### Exceptions

One exceptions register for code-level deviations plus ADRs for design-level ones; every entry has an owner, reason, risk note and expiry; security-relevant entries flow to the ISMS risk register.

<!-- check:compliance -->
### Compliance evidence

Produces the core evidence for ISO/IEC 27001:2022 Annex A change management and secure development controls and SOC 2 change-management criteria: every change has a ticket, a reviewed pull request with named approvers, CI results and (via [[DEP-release-notes-and-change]]) a deploy record. An auditor can sample a production release and trace each commit back to its ticket and approvals using GitHub data alone.

<!-- check:ownership -->
### Ownership and change

Owner: CTO, delegated day to day to the engineering excellence lead. Changes to rulesets or CODEOWNERS are themselves pull requests reviewed by `eng-excellence` and `security`.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Rulesets control how people can interact with branches and tags, including required status checks, required reviews and bypass lists.",
    "id": "R1",
    "kind": "vendor",
    "title": "About rulesets",
    "url": "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets",
    "vendor": "GitHub"
  },
  {
    "excerpt": "Code owners are automatically requested for review when a pull request changes code they own; rulesets can require their approval.",
    "id": "R2",
    "kind": "vendor",
    "title": "About code owners",
    "url": "https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners",
    "vendor": "GitHub"
  }
]
```

<!-- end -->
