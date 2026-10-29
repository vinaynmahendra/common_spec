---
id: "APP-framework-dependencies"
title: "Framework dependencies"
parent: "APP"
order: 2
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: "Approved core libraries and how to use them: Prisma (decision in 19.3), Zod, TanStack Query, React Hook Form; version and upgrade policy"
links: [{"rel": "decided-by", "to": "ADR-orm"}]
rev: 4
syncHash: "c9327a10acc594d9"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.2 Framework dependencies

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Approved core libraries and how to use them: Prisma (decision in 19.3), Zod, TanStack Query, React Hook Form; version and upgrade policy

<!-- section:purpose -->
## Purpose and scope

Lists the approved core libraries for `apps/web` and the shared packages it uses, how each must be used, and the version and upgrade policy. It keeps the stack small and consistent so that security patches, upgrades and onboarding stay manageable. The ORM choice is recorded in [[ADR-orm]].

<!-- section:rules -->
## Rules

1. **DEP-1** Approved core libraries (versions pinned in the pnpm catalog in `pnpm-workspace.yaml`):

   | Concern | Library | Use |
   |---|---|---|
   | Framework | Next.js 16 (App Router), React 19 | Only App Router; no Pages Router |
   | Data access | Prisma ORM ([[ADR-orm]]) | Only through `@nomology/data-access` with the tenant extension ([[MT-prisma-client-extension-wraps]]) |
   | Validation | Zod | One schema per input, shared by client form, Server Action / tRPC procedure and OpenAPI generation |
   | Internal API | tRPC v11 | Routers per persona ([[APP-internal-api-trpc-routers-per]]) |
   | Server state in client | TanStack Query v5 (via tRPC integration) | Interactive client views only ([[APP-client-state-and-data-fetching]]) |
   | Forms | React Hook Form + `@hookform/resolvers/zod` | All forms with more than two fields |
   | i18n | ICU message format library chosen in [[I18N-i18n]] | No string concatenation |
   | Dates | `Temporal` polyfill or date library chosen in [[I18N-l10n]] | No `Date` arithmetic for deadlines; use [[PKG-calendars-and-deadline]] |
   | Telemetry | OpenTelemetry JS | Via `instrumentation.ts` |
   | Workflows client | `@temporalio/client` | Only in server code |
2. **DEP-2** Adding a new runtime dependency to `apps/web` or any package it imports needs a dependency review (licence, maintenance, size, security record, data it sends anywhere) and approval from the frontend lead in CODEOWNERS.
3. **DEP-3** Prisma Client is never imported in `apps/web` directly; only `@nomology/data-access` may import it (Turborepo boundaries).
4. **DEP-4** Raw SQL (`$queryRaw`, `$executeRaw`) is allowed only inside `@nomology/data-access` within the tenant transaction, with a reviewer from platform engineering.
5. **DEP-5** Patch policy: critical security advisories in Next.js, React, Prisma or tRPC are patched in production in all regions within 72 hours; high within 7 days; others with the next regular upgrade.
6. **DEP-6** Minor versions of core libraries are taken at least monthly; major versions within 6 months of release, after a preview-environment run of the full Playwright suite.
7. **DEP-7** No canary or experimental features in production unless listed in this node with a fallback (current list: none beyond `cacheComponents`, which is stable in Next.js 16; `experimental.sri` is under evaluation).

<!-- section:rationale -->
## Rationale

- One validation library across forms, actions, procedures and OpenAPI removes drift between client and server checks.
- The 72-hour window (DEP-5) reflects real incidents such as the critical React Server Components vulnerability disclosed in December 2025 [R1].
- DEP-3 keeps tenant isolation in one place: if pages could import Prisma, a missing tenant extension would be a code-review catch rather than a build failure.

<!-- section:tooling -->
## Tooling and configuration

- pnpm catalogs for single versions across the monorepo; `pnpm-lock.yaml` committed; `onlyBuiltDependencies` allow-list for install scripts
- Renovate (or Dependabot) grouped updates per library family, auto-merge disabled for core libraries
- `turbo boundaries` rules for DEP-3 [R2]
- `pnpm audit` and SCA scanning in CI ([[SEC-vulnerability-management]])
- `size-limit` for bundle impact of new dependencies

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement |
|---|---|
| DEP-1, DEP-2 | CI check: any new entry in a `package.json` under `apps/web` or `packages/*` without a matching entry in `docs/dependencies.md` fails; CODEOWNERS approval |
| DEP-3 | `turbo boundaries` fails the build |
| DEP-4 | ESLint rule bans `$queryRaw`/`$executeRaw` outside `packages/data-access` |
| DEP-5, DEP-6 | Dashboard of open advisories and version lag; weekly review by frontend lead |
| DEP-7 | Lint on `next.config.ts` experimental keys against an allow-list |

<!-- section:exceptions -->
## Exceptions

Requested through a pull request that adds the library to `docs/dependencies.md` with reason, owner and review date. DEP-3 and DEP-4 outside data-access are non-waivable.

<!-- section:adoption -->
## Adoption and migration

New repository, so adoption is from day one. The pnpm catalog and boundaries config are created in Phase 0 ([[PLAN]]).

<!-- section:questions -->
## Open questions

- [ ] Merged from "ORM": Prisma, validation (Zod), data fetching (TanStack Query), forms (React Hook Form) — now folded into DEP-1; confirm and close.
- [ ] Choice of i18n library and date library (owners: [[I18N-i18n]], [[I18N-l10n]])
- [ ] Renovate or Dependabot (owner: DevOps)

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

DEP-1 to DEP-4 and DEP-7 are tool-enforced (dependency allow-list check, Turborepo boundaries, ESLint, config lint); DEP-5 and DEP-6 are measured on a dashboard and reviewed weekly.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

DEP-3 and DEP-4 keep all database access behind the tenant-scoped extension; `onlyBuiltDependencies` and lockfile review limit supply-chain risk from install scripts.

<!-- check:compliance -->
### Compliance evidence

Supports ISO 27001:2022 Annex A 8.8 (management of technical vulnerabilities) through the patch windows and audit records, and 8.28 (secure coding) through the approved-library list.

<!-- check:ownership -->
### Ownership and change

Owner: frontend lead; Prisma usage co-owned with platform engineering; reviewed at every major upgrade of Next.js or React and at least yearly.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "title": "Critical security vulnerability in React Server Components",
    "url": "https://react.dev/blog/2025/12/03/critical-security-vulnerability-in-react-server-components",
    "vendor": "Meta (React)"
  },
  {
    "id": "R2",
    "kind": "vendor",
    "title": "Turborepo reference: boundaries",
    "url": "https://turbo.build/repo/docs/reference/boundaries",
    "vendor": "Vercel (Turborepo)"
  }
]
```

<!-- end -->
