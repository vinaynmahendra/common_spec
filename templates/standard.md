# Template: Engineering standard (`standard`)

Generated from `standard.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies a rule the engineering team follows, with the reasoning, the tooling that enforces it and the way to ask for an exception.

**Depth:** 1–4 pages. Rules must be checkable; prefer rules enforced by tooling over rules enforced by review. Keep the rationale short. If a rule needs debate, link a Decision record.

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose and scope (level 1)

What the standard covers and why it exists.

Illustrative example (not a requirement):

> Defines how the monorepo is laid out so any engineer can find code, and so builds stay fast and dependencies stay one-directional.

### `rules` Rules (level 1)

Numbered, imperative, checkable rules.

Illustrative example (not a requirement):

> - STD-REPO-1 Apps live in `apps/*`, shared libraries in `packages/*`, infrastructure in `infra/*`
> - STD-REPO-2 `packages/*` must not import from `apps/*`
> - STD-REPO-3 Each package has a `README.md` with purpose, public API and owner
> - STD-REPO-4 Workspace dependencies use `workspace:*`; no relative imports across packages

### `rationale` Rationale (level 2)

Why each non-obvious rule exists.

Illustrative example (not a requirement):

> STD-REPO-2 keeps the dependency graph acyclic, which lets Turborepo cache package builds and lets us publish packages independently later.

### `tooling` Tooling and configuration (level 1)

Tools, config files and versions.

Illustrative example (not a requirement):

> Turborepo, pnpm workspaces, ESLint `import/no-restricted-paths` for STD-REPO-2, `turbo.json` pipeline at repo root.

### `enforcement` Enforcement (level 1)

Which rules are enforced where (pre-commit, CI, code review) and what fails.

Illustrative example (not a requirement):

> | Rule | Enforced by | Failure |
> |---|---|---|
> | STD-REPO-2 | ESLint in CI | Build fails |
> | STD-REPO-3 | CI script checks README exists | Build fails |
> | STD-REPO-1 | Code review | Reviewer blocks |

### `examples` Examples (level 2)

Good and bad examples.

Illustrative example (not a requirement):

> Good: `apps/case-portal` imports `@platform/notifications`.
> Bad: `packages/notifications` imports a type from `apps/case-portal/types`. Move the type into the package.

### `exceptions` Exceptions (level 2)

How to request a deviation and how it is recorded.

Illustrative example (not a requirement):

> Add an ESLint disable with a ticket reference; approved by a tech lead; reviewed monthly.

### `adoption` Adoption and migration (level 3)

How existing code is brought into line.

Illustrative example (not a requirement):

> Existing CORD services migrate in phase 2; new code follows the standard from day one.

### `questions` Open questions (level 3)

Checklist.

Illustrative example (not a requirement):

> - [ ] Do Temporal workers live in `apps/workers` or per domain?

## Checks

### `enforcement` Enforcement

**Question:** For each numbered rule, which tool checks it automatically, at which stage, and what exactly fails when it is broken?

- For every rule, is it enforced by a tool (ESLint rule, TypeScript compiler option, Turborepo boundaries, Prisma schema check, CI job, repository template, GitHub ruleset) or only by human review? Mark each one.
- At which stage does each check run (editor, pre-commit, pull request CI, merge queue, deploy pipeline), and is the CI check marked as required so it cannot be bypassed?
- Do the checks run on the whole monorepo or only on affected packages, and can a change in a shared package skip checks for the apps that import it?
- Who can override a failing required check or merge without approval (admins, bypass lists in rulesets), and is every bypass logged?
- For rules that cannot be automated, what is the review checklist item, and who (CODEOWNERS) is required to approve?
- How are the tool configurations themselves protected from being weakened in a pull request (for example disabling a lint rule or lowering a coverage threshold)?

**Good answer:** A table mapping each rule number to its enforcing tool, configuration file, stage and failure message, with review-only rules clearly marked and kept to a minimum. Required checks are set in GitHub rulesets, bypass is limited to named roles and logged, and changes to lint, tsconfig and CI configuration require approval from the standard's owner via CODEOWNERS.

**Red flags:**

- Most rules enforced only by 'reviewers should check'
- CI checks that run but are not required for merge
- Any engineer can disable a rule inline with no justification or tracking
- Admins routinely bypass branch protection

### `guardrails` Security, tenancy and privacy guardrails

**Question:** Does this standard build in the platform's non-negotiable protections (tenant isolation, secrets, personal data, supply chain) where its subject touches them, rather than leaving them to other documents?

- Where the standard covers code or data access, does it require tenant-scoped data access through the shared Prisma extension and forbid raw queries that bypass Row-Level Security?
- Where it covers CI/CD or environments, does it require secret scanning, no secrets in the repo or in build logs, pinned and scanned dependencies, and builds from a trusted pipeline with provenance?
- Where it covers migrations, does it require backwards-compatible (expand then contract) changes and RLS policies on every new tenant table?
- Where it covers logging, frontend or testing, does it forbid personal data in logs, fixtures and screenshots, and require synthetic test data?
- Where it covers frontend, does it require WCAG 2.2 AA checks?
- Which of these protections are enforced by a tool (see Enforcement) rather than stated only?

**Good answer:** Lists the protections relevant to this standard's subject, each written as a checkable rule with its enforcing tool, and links to the platform security and tenancy nodes for detail. For CI/CD and dependency standards, it states the supply-chain target (for example SLSA Build Level 2 provenance and blocking high-severity vulnerabilities).

**Red flags:**

- A migration standard with no rule about RLS on new tables
- A CI/CD standard with no secret scanning or dependency scanning
- Test or seed data copied from production

### `onboarding` Onboarding and usability

**Question:** Can a new engineer, or a coding assistant, follow this standard correctly using only this node and the tooling it points to, on their first day?

- Is there a quick-start (commands to install tools, run checks locally, fix common failures) that works on a clean machine, and when was it last tried by someone new?
- Does each rule have a good and a bad example in our own codebase style (TypeScript, Next.js, Prisma), not a generic one?
- Do tool error messages point back to the rule number and this node so a failing check explains itself?
- Are auto-fixes available (lint --fix, codemods, generators/templates for new packages and apps) so following the rule is the easy path?
- Is the standard written so it can be loaded as context by AI coding assistants (short imperative rules, no ambiguity), and is that file kept in sync with this node?
- Is there a named owner or channel for questions?

**Good answer:** Contains a tested quick-start, examples drawn from our repo, error messages that link to rule numbers, and generators or auto-fixes for the common cases. States who last ran through it as a newcomer and when, and where the assistant-readable version lives.

**Red flags:**

- Rules that require knowledge held only by senior engineers
- Quick-start never tested on a fresh machine
- Failing checks with messages that do not say which rule or how to fix

### `exceptions` Exceptions

**Question:** Is there a written, lightweight way to deviate from a rule that records who approved it, why, and when it expires?

- How does an engineer request an exception (inline suppression with a required comment, an exceptions file, a Decision record), and who can approve?
- Does every exception carry an owner, a reason, a risk note and an expiry or review date?
- Is there a tool that lists all current exceptions and flags expired ones (for example a lint rule requiring a ticket ID on every eslint-disable)?
- Are some rules non-waivable (for example tenant isolation, secrets in code), and is that stated?
- How are exceptions that affect security or compliance reported to the information security owner for the ISO 27001 / SOC 2 risk register?

**Good answer:** Describes the exception mechanism with a required format (owner, reason, ticket, expiry), names approvers by role, lists non-waivable rules, and points to an automated report of active and expired exceptions that is reviewed on a set cadence.

**Red flags:**

- Silent inline disables with no reason
- Exceptions with no expiry
- No list of rules that cannot be waived

### `compliance` Compliance evidence

**Question:** Which audit or certification requirements does this standard help satisfy, and what evidence does following it produce automatically?

- Which ISO 27001:2022 Annex A controls or SOC 2 criteria does this standard support (for example secure development, change management, configuration management, separation of environments)?
- What evidence is produced as a side effect (CI run history, pull request approvals, signed build provenance, scan reports), where is it stored, and for how long?
- Could an auditor sample a change and trace it from ticket to pull request to review to deploy using that evidence?
- Does the standard support specific client or regulator expectations (for example SEBI ODR or arbitral institution security questionnaires, ISO 42001 for AI-related code)?
- Who is told when the standard changes so that compliance documentation stays current?

**Good answer:** Maps the standard to the specific controls it supports and names the evidence artefacts and their retention. Demonstrates that a sampled change can be traced end to end without manual collection.

**Red flags:**

- Evidence depends on screenshots collected by hand before audits
- No mapping to controls even though the standard covers change management or secure development

### `measurement` Adoption measurement

**Question:** How do we know how much of the codebase actually follows this standard today, and is that number moving the right way?

- What metric shows compliance (number of violations, packages fully migrated, percentage of services on the template, active exceptions)?
- Is there a baseline or 'ratchet' so existing violations are allowed but new ones are blocked?
- Where is the metric shown and who reviews it, how often?
- What is the target and date for full adoption, and what happens to code that has not migrated by then?
- Does the standard affect delivery measures (build time, deploy frequency, change failure rate) and are those watched for regressions?

**Good answer:** Names a concrete metric, its current value, the target and date, and the dashboard or report where it is reviewed. Uses a ratchet so the count of violations can only decrease.

**Red flags:**

- No idea how many places violate the rule
- A 'big bang' migration with no tracking
- New violations allowed while old ones are being fixed

### `ownership` Ownership and change

**Question:** Who owns this standard, how are changes to it proposed and approved, and how is it kept current with the tools it relies on?

- Who is the named owner (person or team), and who must approve changes?
- Is the standard versioned, with a change log that says what changed, why and from when it applies?
- How often is it reviewed (at least yearly, and when a tool it depends on has a major version change)?
- How are engineers told about changes, and are tooling configurations updated in the same change as the text so they never disagree?
- Which other standards or nodes depend on this one, and are they checked for conflicts when it changes?

**Good answer:** Names the owner and approvers, links the change log, states the review cadence and last review date, and requires that text and tool configuration change in the same pull request.

**Red flags:**

- No owner
- Document says one thing and the lint or CI configuration enforces another
- Not reviewed for more than a year

