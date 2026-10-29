---
id: "FND-monorepo"
title: "Monorepo"
parent: "FND"
order: 1
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: "Turborepo + pnpm workspaces (`apps/`, `packages/`)"
links: []
rev: 2
syncHash: "4bef902e6fe2dd93"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 1.1 Monorepo

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Turborepo + pnpm workspaces (`apps/`, `packages/`)

<!-- section:purpose -->
## Purpose and scope

Defines how the platform repository is organised: one Turborepo + pnpm workspace with deployable `apps/`, shared `packages/` and build `tooling/`. It exists so that every engineer and coding assistant finds code in the same place, packages can only depend on each other in allowed directions, and CI only rebuilds what a change affects. It covers layout, package naming and metadata, dependency rules, `turbo.json` tasks and the remote cache. Coding conventions inside files are in [[FND-language-and-conventions]].

<!-- section:rules -->
## Rules

**Layout**

```text
/
├─ apps/
│  ├─ web/               Next.js App Router; all persona route groups (see APP-route-groups-per-persona)
│  ├─ worker-temporal/   Temporal workers; one entry point per task queue: cases, hearings, documents, ai-pipelines, billing
│  ├─ worker-jobs/       BullMQ workers: notifications, malware scan, thumbnails, search indexing, webhooks
│  ├─ doc-viewer/        Sandboxed document origin (APP-document-viewer-and-sandbox)
│  └─ developer-portal/  Public API and webhook documentation (DOC-api-documentation-openapi)
├─ packages/
│  ├─ db/                Prisma schema, migrations (with RLS SQL), tenant client extension
│  ├─ env/               Zod environment schemas and loader
│  ├─ <platform>/        auth, authz, audit, storage, cache, settings, feature-flags, notifications, search,
│  │                     rules, calendars, retention, i18n, content, ui, observability, ai, workflows, jobs,
│  │                     api-contracts, security
│  ├─ domain-<name>/     cases, documents, hearings, neutrals, transcribers, billing
│  └─ testing/           fixture tenants, factories, isolation test kit
├─ tooling/              tsconfig, eslint-config, prettier-config, generators (turbo gen templates)
└─ docs/                 architecture (arc42), runbooks, ADR index
```

**Rules**
- **MONO-1** Every deployable unit lives in `apps/<name>`; every shared library in `packages/<name>`; every config-only package in `tooling/<name>`. Nothing else at the root except workspace config files and `docs/`.
- **MONO-2** Package names are `@nomology/<folder-name>`, every package is `"private": true`, and every package declares an `exports` map. Importing a path not listed in `exports` is a build error.
- **MONO-3** Every `package.json` carries exactly one layer tag (`layer:app`, `layer:domain`, `layer:platform`, `layer:tooling`) and one runtime tag (`runtime:server`, `runtime:client`, `runtime:universal`) in `turbo.json` `tags`.
- **MONO-4** Allowed import directions: app → domain → platform → tooling. A platform package never imports a domain package; a domain package never imports another domain package's internals (only its `exports`, and cross-domain writes go through domain events or workflows, see [[WF-separation-of-concerns-temporal]]).
- **MONO-5** A `runtime:client` package never imports a `runtime:server` package. Server-only packages start their entry file with `import 'server-only'`.
- **MONO-6** Only `@nomology/db` depends on `prisma` or `@prisma/client`.
- **MONO-7** Internal dependencies use `workspace:*`. Third-party versions shared by more than one package are declared once in the pnpm `catalog:` in `pnpm-workspace.yaml`.
- **MONO-8** The lockfile is committed and CI installs with `pnpm install --frozen-lockfile`. Dependency lifecycle scripts are blocked except for packages listed in `onlyBuiltDependencies`.
- **MONO-9** Every package defines the standard scripts `build`, `lint`, `typecheck`, `test` (and `test:integration` where it touches Postgres, Redis or Temporal). `turbo.json` declares their inputs, outputs and the environment variables each task reads; strict environment mode is on.
- **MONO-10** New apps and packages are created with `pnpm turbo gen package` / `pnpm turbo gen app` from templates in `tooling/generators`, which add tags, scripts, `tsconfig`, ESLint config, CODEOWNERS entry and a README stub.
- **MONO-11** The remote cache requires signed artefacts; caches are never shared with forks.
- **MONO-12** A new third-party runtime dependency in a `layer:platform` or `layer:domain` package needs approval from the package owner and, for packages on the approved core list in [[APP-framework-dependencies]], an ADR.

<!-- section:rationale -->
## Rationale

- **MONO-4 and MONO-6** keep tenant isolation in one place. If any package could open its own Prisma client, it could skip the transaction-scoped tenant setting of [[MT-prisma-client-extension-wraps]] and rely on luck rather than RLS context.
- **MONO-5** stops server code (database clients, secrets, KMS helpers) from being bundled into browser JavaScript, where it would leak configuration or fail at runtime.
- **MONO-8** reduces supply-chain risk: install scripts are a common route for malicious packages, and a frozen lockfile makes builds reproducible.
- **MONO-9** strict environment mode makes Turborepo hash only declared variables, so a cache hit cannot hide a build that depended on an undeclared value.
- **MONO-11** a poisoned cache entry would be replayed into every build; signatures stop that.

<!-- section:tooling -->
## Tooling and configuration

| Tool | Version policy | Config |
|---|---|---|
| Node.js | Current Active LTS, pinned (proposed: Node.js 24 LTS) | `.nvmrc`, `engines.node` in root `package.json` |
| pnpm | Pinned major (proposed: pnpm 10) | `packageManager` field (Corepack), `pnpm-workspace.yaml` with `packages`, `catalog`, `onlyBuiltDependencies` |
| Turborepo | Pinned 2.x | `turbo.json` (tasks, `tags`, `boundaries`, strict env), `TURBO_REMOTE_CACHE_SIGNATURE_KEY` from CI secrets |
| dependency-cruiser | Backstop for rules `turbo boundaries` cannot express | `tooling/dependency-rules/.dependency-cruiser.cjs` |
| Renovate | Grouped weekly updates, security updates immediately | `renovate.json` |
| Generators | `turbo gen` with Plop templates | `tooling/generators/` |

Sketch of `turbo.json`:

```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["tooling/tsconfig/**", "tooling/eslint-config/**"],
  "tasks": {
    "build": { "dependsOn": ["^build"], "outputs": ["dist/**", ".next/**", "!.next/cache/**"] },
    "typecheck": { "dependsOn": ["^build"] },
    "lint": {},
    "test": { "dependsOn": ["^build"], "outputs": ["coverage/**"] },
    "test:integration": { "dependsOn": ["^build"], "env": ["DATABASE_URL", "REDIS_URL", "TEMPORAL_ADDRESS"] }
  },
  "boundaries": {
    "tags": {
      "layer:platform": { "dependencies": { "deny": ["layer:domain", "layer:app"] } },
      "layer:domain":   { "dependencies": { "deny": ["layer:app"] } },
      "runtime:client": { "dependencies": { "deny": ["runtime:server"] } }
    }
  }
}
```
Exact `boundaries` syntax to be checked against the pinned Turborepo version [R1].

<!-- section:enforcement -->
## Enforcement

| Rule | Where | What fails |
|---|---|---|
| MONO-1, MONO-3 | CI `repo-structure` script | Unknown top-level folder, package without exactly one layer and one runtime tag |
| MONO-2 | TypeScript (`exports` + `moduleResolution: bundler`) and ESLint `import/no-internal-modules` | Deep import into another package |
| MONO-4, MONO-5 | `turbo boundaries` (required check); dependency-cruiser for domain-to-domain internals | Forbidden dependency edge |
| MONO-6 | ESLint `no-restricted-imports` in shared config; dependency-cruiser | Any import of `@prisma/client` outside `packages/db` |
| MONO-7, MONO-8 | `pnpm install --frozen-lockfile`; `syncpack lint` for catalog use | Lockfile drift; duplicate version declarations |
| MONO-9 | CI `turbo run ... --affected`; strict env mode | Missing script; task reading an undeclared env var |
| MONO-10 | CODEOWNERS on `apps/` and `packages/` roots require platform review for new folders | New package without generator scaffolding is caught in review |
| MONO-11 | Turborepo signature verification | Unsigned or tampered cache artefact is ignored and the task re-runs |
| MONO-12 | GitHub dependency-review action plus CODEOWNERS on `package.json` of platform packages | New dependency without owner approval |

All CI checks are required in the `main` ruleset [R2]. Changes to `turbo.json`, `pnpm-workspace.yaml` and `tooling/**` are owned by the engineering excellence group in CODEOWNERS, so weakening a check needs their approval.

<!-- section:examples -->
## Examples

Good: a domain package reads tenant data only through the db package.

```ts
// packages/domain-cases/src/list-cases.ts
import { withTenant } from '@nomology/db';
export const listOpenCases = (ctx: TenantContext) =>
  withTenant(ctx, (tx) => tx.case.findMany({ where: { status: 'OPEN' } }));
```

Bad: a platform package reaching into a domain package and opening its own client.

```ts
// packages/notifications/src/send.ts
import { PrismaClient } from '@prisma/client';          // MONO-6: forbidden
import { getCase } from '@nomology/domain-cases/src/x'; // MONO-2 + MONO-4: deep import, wrong direction
```

<!-- section:exceptions -->
## Exceptions

Exceptions are requested in the pull request that needs them, recorded in `tooling/dependency-rules/exceptions.yaml` with `rule`, `path`, `owner`, `reason`, `ticket` and `expires` fields, and approved by the engineering excellence owner. CI fails when an exception is past its expiry date. MONO-5 and MONO-6 are non-waivable. See [[FND-governance#exceptions]] for the general process.

<!-- section:adoption -->
## Adoption and migration

The repository is new, so rules apply from the first commit. Code migrated from the current CORD and TERES codebases enters through a `packages/legacy-*` holding area tagged `layer:domain` with a dated exception per rule it breaks; each legacy package has a removal target in the delivery plan.

<!-- section:questions -->
## Open questions

- [ ] Remote cache: self-hosted (S3-backed, in our account) or Vercel Remote Cache? Decide by Phase 0 step 0b.
- [ ] Internal packages compiled to `dist/` (tsup) or consumed as TypeScript source (just-in-time) by Next.js and workers? Proposal: compiled for anything a worker imports.
- [ ] Does `infra/` (Terraform) live in this repo or a separate one with tighter access?
- [ ] Confirm Node.js and pnpm versions at Phase 0 kick-off.
- [ ] Is `apps/developer-portal` part of this repo or a separate static site repo?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Every rule except MONO-10 and MONO-12 is tool-enforced (see Enforcement table); those two are enforced by CODEOWNERS approval on new folders and on platform `package.json` files. All checks run on pull requests and again in the merge queue. Affected-only runs are safe because changes to `tooling/**`, root config or `packages/db` force a full run (declared in `globalDependencies` and a CI path filter). Ruleset bypass is limited to the release-admin group and every bypass appears in the GitHub audit log reviewed monthly by the information security owner.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Tenant isolation: MONO-6 confines Prisma to `packages/db`, where the tenant extension lives ([[MT-prisma-client-extension-wraps]]). Supply chain: frozen lockfile, blocked install scripts, dependency review, Renovate with grouped updates and signed remote cache [R3]. Secrets: strict env mode means variables are declared per task, and secret values are never inputs to cacheable tasks (see [[FND-environment-management#rules]]).

<!-- check:onboarding -->
### Onboarding and usability

New packages and apps come from `turbo gen`, so the correct tags, scripts and configs are the default. Boundary errors from `turbo boundaries` and ESLint name the rule (for example "MONO-6: import @prisma/client only inside packages/db") and link to this node. A short `AGENTS.md` / `CLAUDE.md` at the repo root restates MONO-1 to MONO-12 for coding assistants and is generated from this node so the two never disagree.

<!-- check:exceptions -->
### Exceptions

Exceptions live in one YAML file with owner, reason, ticket and expiry; CI lists them on every run and fails on expired entries. MONO-5 and MONO-6 cannot be waived because they protect secrets and tenant isolation.

<!-- check:measurement -->
### Adoption measurement

Metrics: number of active boundary exceptions (target 0 outside `legacy-*`), share of packages created by generator (target 100%), remote cache hit rate on PR CI (target above 70%), and PR CI duration p50/p95 (targets in [[FND#goals]]). Shown on the engineering health dashboard and reviewed at the fortnightly engineering leads meeting.

<!-- check:ownership -->
### Ownership and change

Owner: engineering excellence lead (to be named). Changes to this standard and to `turbo.json`, `pnpm-workspace.yaml` and `tooling/**` are made in the same pull request so text and config never drift. Reviewed yearly and on every Turborepo or pnpm major upgrade.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "Boundaries let a repository declare tags and rules for which packages may depend on which, checked with `turbo boundaries`.",
    "id": "R1",
    "kind": "vendor",
    "title": "Turborepo reference: boundaries",
    "url": "https://turbo.build/repo/docs/reference/boundaries",
    "vendor": "Vercel (Turborepo)"
  },
  {
    "excerpt": "Rulesets control how people can interact with branches and tags, including required status checks, required reviews and bypass lists.",
    "id": "R2",
    "kind": "vendor",
    "title": "About rulesets",
    "url": "https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets",
    "vendor": "GitHub"
  },
  {
    "excerpt": "Recommends enforcing the lockfile, minimising install-script attack surface and auditing dependencies.",
    "id": "R3",
    "kind": "web",
    "publisher": "OWASP",
    "title": "NPM Security Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/NPM_Security_Cheat_Sheet.html"
  }
]
```

<!-- end -->
