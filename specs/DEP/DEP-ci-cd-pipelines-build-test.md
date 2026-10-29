---
id: "DEP-ci-cd-pipelines-build-test"
title: "CI/CD pipelines (build, test, scan, deploy)"
parent: "DEP"
order: 1
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: ""
links: []
rev: 2
syncHash: "df03de423b0fcd3e"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 15.1 CI/CD pipelines (build, test, scan, deploy)

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

<!-- section:purpose -->
## Purpose and scope

Specifies the pipelines that check every pull request, build the release artefacts once on `main`, and deploy them. It covers stages, required checks, artefact build, SBOM, signing and provenance, pipeline identity and pipeline performance. Promotion between environments is in [[DEP-environment-promotion-and-multi]]; traffic shifting is in [[DEP-blue-green-canary-releases]].

<!-- section:rules -->
## Rules

**Pull request pipeline** (`.github/workflows/pr.yml`)
- **CICD-1** Install with `pnpm install --frozen-lockfile`, then run `turbo run lint typecheck test build --affected`. A change to `packages/db`, `tooling/**`, root config files or `.github/**` runs the full graph.
- **CICD-2** Required checks on every PR: `lint`, `typecheck`, `unit`, `integration` (Postgres behind PgBouncer in transaction mode, Redis, Temporal dev server as service containers), `boundaries`, `migration-lint`, `rls-catalogue` ([[TST-multi-tenant-isolation-tests]]), `secret-scan`, `sast`, `dependency-review`, `openapi-diff` (when contracts change), `i18n-extract`, `bundle-budget` ([[APP-frontend-performance-budgets]]), `a11y-components`, `pr-checklist`.
- **CICD-3** When the PR touches `apps/web` or a package it depends on, a preview environment is deployed and `e2e-smoke` and `a11y-journeys` run against it ([[DEP-preview-environments-per-pr]]).
- **CICD-4** Merges go through the merge queue, which re-runs required checks on the combined result.

**Main pipeline** (`.github/workflows/main.yml`)
- **CICD-5** Build each deployable (`web`, `worker-temporal`, `worker-jobs`, `doc-viewer`, `migrate`) once as an OCI image from a pinned, digest-referenced base image. Next.js uses `output: 'standalone'`. Images run as non-root with a read-only root filesystem.
- **CICD-6** For every image: generate a CycloneDX SBOM, scan with Trivy (fail on critical or high vulnerabilities with a fix available, and on embedded secrets), sign with cosign keyless signing through GitHub OIDC, and attach a build provenance attestation [R1].
- **CICD-7** Push images by digest to the registry in each region (ECR per AWS region, ACR for Azure deployments). Tags are informational; deploys reference digests only.
- **CICD-8** Deploy automatically to dev; every later environment is a promotion of the same digests.

**Pipeline security**
- **CICD-9** Workflows authenticate to AWS and Azure with OIDC federation to roles scoped per GitHub environment; no long-lived cloud keys exist in GitHub secrets.
- **CICD-10** Third-party actions are pinned to a full commit SHA; workflow `permissions` default to `contents: read` and are widened per job.
- **CICD-11** PRs from forks run without secrets and without preview deploys.
- **CICD-12** Build logs must not print secrets or personal data; test fixtures are synthetic only.

**Pipeline health**
- **CICD-13** A test that fails then passes on retry is marked flaky automatically, quarantined within one working day with a ticket, and must be fixed or deleted within 10 working days.
- **CICD-14** Proposed targets: PR pipeline p50 under 12 minutes, p95 under 20 minutes; main pipeline to dev under 25 minutes.

<!-- section:rationale -->
## Rationale

- **CICD-5 to CICD-7** Building once and deploying by digest is what makes the staging test meaningful for production, and signatures let each region's deploy step check that the image came from our pipeline, as recommended by SLSA build level 2 and the NIST SSDF [R1] [R2].
- **CICD-9, CICD-10** Pipeline credentials and mutable action tags are common supply-chain attack routes [R3].
- **CICD-2 integration** RLS context bugs only appear with real Postgres and PgBouncer in transaction mode; mocks hide them.

<!-- section:tooling -->
## Tooling and configuration

| Concern | Tool |
|---|---|
| CI platform | GitHub Actions with larger runners for integration and e2e jobs (assumed; ADR to confirm) |
| Task orchestration and caching | Turborepo with signed remote cache ([[FND-monorepo]]) |
| SAST | CodeQL (JavaScript/TypeScript) plus Semgrep rules for our own patterns (raw SQL, missing `withTenant`) |
| Secrets | gitleaks; GitHub secret scanning with push protection |
| Dependencies | GitHub dependency review (blocks high-severity advisories and disallowed licences); Renovate |
| Migrations | `squawk` Postgres migration linter, custom RLS checker, `prisma migrate diff` ([[DEP-database-migration-strategy-zero]]) |
| Images | Docker Buildx, Trivy, Syft (CycloneDX), cosign, `actions/attest-build-provenance` |
| Contracts | `oasdiff` for OpenAPI breaking changes ([[DOC-api-documentation-openapi]]) |

<!-- section:enforcement -->
## Enforcement

Required checks are configured in the `main` ruleset [R4]; the merge queue re-runs them. Deploy jobs verify the cosign signature and provenance before calling ECS or Container Apps, and refuse unsigned images. Workflow files are owned by `eng-excellence` and `devops` in CODEOWNERS, so disabling a check needs their approval. A scheduled job compares the ruleset's required checks with this list and alerts on drift.

<!-- section:examples -->
## Examples

Good: `- uses: actions/checkout@<40-character SHA> # v4.x` with `permissions: { contents: read }`.

Bad: `- uses: some-org/deploy-action@main` with `AWS_SECRET_ACCESS_KEY` stored as a repository secret.

<!-- section:exceptions -->
## Exceptions

A required check can be temporarily non-blocking only through an exceptions entry with owner and expiry (maximum 10 working days) approved by `eng-excellence`. Security gates (secret scan, signing, critical vulnerabilities with a fix) are non-waivable; a critical vulnerability with no fix available is accepted only through [[SEC-vulnerability-management]] with a dated risk acceptance.

<!-- section:questions -->
## Open questions

- [ ] Confirm GitHub Actions as CI platform (assumed throughout) and whether self-hosted runners are needed for any job.
- [ ] Coverage thresholds: per package or global? Proposal in [[TST-unit-integration-contract-and]].
- [ ] Do we target SLSA build level 3 (hardened builder) for audit, or is level 2 sufficient for client questionnaires?
- [ ] How long are build logs, SBOMs and attestations retained for audit evidence?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

All PR checks listed in CICD-2 are required status checks in the ruleset and re-run in the merge queue; deploy jobs verify signatures. Affected-only runs cannot skip consumers because Turborepo's graph includes dependents and changes to shared tooling force full runs. Bypass is limited to `release-admins` and logged.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Secrets: OIDC instead of static keys, gitleaks, push protection, image secret scanning, no secrets for fork PRs. Supply chain: frozen lockfile, SHA-pinned actions, dependency review, SBOM, signing and provenance. Tenant isolation: integration tests on real Postgres with forced RLS behind PgBouncer, plus the RLS catalogue check. Personal data: synthetic fixtures only (CICD-12).

<!-- check:onboarding -->
### Onboarding and usability

Each required check can be reproduced locally with one command (`pnpm ci:lint`, `pnpm ci:integration` using Docker Compose). Check names match `turbo` task names, and failure annotations link to the rule ID.

<!-- check:compliance -->
### Compliance evidence

Evidence produced automatically: CI run history per PR, required-check results, signed provenance per image, SBOMs and scan reports. Together with PR approvals this supports ISO/IEC 27001:2022 secure development and change management controls and SOC 2 change-management criteria.

<!-- check:measurement -->
### Adoption measurement

Tracked weekly: PR pipeline p50/p95 duration, flaky test count and age, cache hit rate, share of images deployed with verified signatures (target 100%), and open critical/high image vulnerabilities.

<!-- check:ownership -->
### Ownership and change

Owner: DevOps lead; `eng-excellence` co-owns workflow files. Reviewed quarterly and when GitHub Actions or a scanner has a major change.

<!-- citations -->
## Citations

```json
[
  {
    "body": "OpenSSF",
    "excerpt": "Build levels describe increasing guarantees: provenance exists (L1), is generated by a hosted build platform and signed (L2), and the build platform is hardened (L3).",
    "id": "R1",
    "ident": "SLSA",
    "kind": "standard",
    "title": "SLSA security levels",
    "url": "https://slsa.dev/spec/v1.0/levels",
    "version": "1.0"
  },
  {
    "body": "NIST",
    "excerpt": "Recommends practices such as protecting all forms of code from unauthorised access and tampering, and verifying third-party components.",
    "id": "R2",
    "ident": "SP 800-218",
    "kind": "standard",
    "title": "Secure Software Development Framework (SSDF)",
    "url": "https://csrc.nist.gov/pubs/sp/800/218/final",
    "version": "1.1"
  },
  {
    "excerpt": "Guidance on securing pipelines: least-privilege pipeline identities, protected secrets, pinned dependencies and actions, and signed artefacts.",
    "id": "R3",
    "kind": "web",
    "publisher": "OWASP",
    "title": "CI/CD Security Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/CI_CD_Security_Cheat_Sheet.html"
  },
  {
    "excerpt": "Rulesets control how people can interact with branches and tags, including required status checks, required reviews and bypass lists.",
    "id": "R4",
    "kind": "vendor",
    "title": "About rulesets",
    "url": "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets",
    "vendor": "GitHub"
  }
]
```

<!-- end -->
