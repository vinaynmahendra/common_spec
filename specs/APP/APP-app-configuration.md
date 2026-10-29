---
id: "APP-app-configuration"
title: "App configuration"
parent: "APP"
order: 1
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: "Parent standard for how apps/web is configured: next.config, proxy, route groups, headers and rendering; details live in the five child nodes"
links: []
rev: 3
syncHash: "2dbdffcd07c6ea9a"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 2.1 App configuration

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Parent standard for how apps/web is configured: next.config, proxy, route groups, headers and rendering; details live in the five child nodes

<!-- section:purpose -->
## Purpose and scope

This standard groups the configuration of `apps/web` that every route group depends on. It sets the few rules that cut across its children and points to them for detail:

| Child | Covers |
|---|---|
| [[APP-app-router-next-config]] | `next.config.ts`, `proxy.ts`, `instrumentation.ts`, root layout, build output |
| [[APP-route-groups-per-persona]] | Route-group map, URL prefixes, persona defaults |
| [[APP-security-headers-csp-cors]] | Response headers, CSP, CORS |
| [[APP-rendering-and-caching-strategy]] | Rendering mode, cache keys, cache handler, version skew |

Environment variables and secrets follow [[FND-environment-management]]; this node only says which of them the app reads.

<!-- section:rules -->
## Rules

1. **APPCFG-1** There is one `next.config.ts` in `apps/web`, typed with `NextConfig`. No per-environment config files; differences come from validated environment variables.
2. **APPCFG-2** All runtime configuration is read through `@nomology/config` (Zod-validated at start-up, see [[FND-environment-management]]). Code in `apps/web` may not read `process.env` directly.
3. **APPCFG-3** Only variables listed in `apps/web/env.public.ts` may carry the `NEXT_PUBLIC_` prefix. The list holds no secrets, no internal hostnames and no tenant data.
4. **APPCFG-4** Configuration that differs per tenant (branding, terminology, feature availability) is never build-time configuration; it is read at request time from [[PKG-settings]], [[PKG-branding-and-theming]] and [[PKG-feature-flags]].
5. **APPCFG-5** Configuration that differs per region (database, Redis, Temporal namespace, collectors, sandbox origin, CDN host) is injected at deploy time by the region's infrastructure stack ([[INF-cloud-and-iac]]). The same image runs in every region.
6. **APPCFG-6** The build is reproducible: `deploymentId` is the git commit SHA, and the same image is promoted from staging to UAT to production ([[DEP-environment-promotion-and-multi]]).

<!-- section:rationale -->
## Rationale

- One image for all regions (APPCFG-5, APPCFG-6) means a fix verified in staging is the exact artefact that reaches India, Singapore and US production, which simplifies change-management evidence for ISO 27001.
- Banning direct `process.env` (APPCFG-2) catches missing configuration at start-up instead of on the first request that needs it, and keeps a single list of what the app reads.
- `NEXT_PUBLIC_` values are inlined into the browser bundle at build time, so they cannot vary per region or tenant anyway, and anything placed there is public (APPCFG-3).

<!-- section:tooling -->
## Tooling and configuration

- Next.js 16 (App Router) with `output: 'standalone'`, see [[APP-app-router-next-config]]
- `@nomology/config` package: Zod schemas, `loadConfig()` called from `instrumentation.ts` `register()`
- ESLint: `n/no-process-env` enabled for `apps/web/**`, with `packages/config/**` allowed
- CI script `check-public-env.ts`: fails if any `NEXT_PUBLIC_*` reference is not in `env.public.ts`, or if a value matches the secret-scanning patterns

<!-- section:enforcement -->
## Enforcement

| Rule | Where | What fails |
|---|---|---|
| APPCFG-1 | CI (`turbo run lint`) | Lint error on any `next.config.*` other than `apps/web/next.config.ts` |
| APPCFG-2 | Editor, pre-commit, CI | ESLint `n/no-process-env` |
| APPCFG-3 | CI | `check-public-env.ts` exit code 1 |
| APPCFG-4 | Code review (CODEOWNERS: frontend lead) | Review checklist item "no tenant data in build-time config" |
| APPCFG-5, 6 | Deploy pipeline | Image digest in production must equal the digest approved in staging |

<!-- section:exceptions -->
## Exceptions

Exceptions use the repo-wide process in [[FND-governance]]: an inline `eslint-disable-next-line` must carry a ticket ID and expiry, and the exceptions report lists them. APPCFG-3 and APPCFG-5 are non-waivable.

<!-- section:questions -->
## Open questions

- [ ] Do Azure Container Apps deployments need any build-time difference (for example image registry or base image), or can APPCFG-5 hold there too? (owner: platform engineering)
- [ ] Should UAT run the production image with production-like region config per client, or a shared UAT per region? (owner: DevOps, see [[FND-environments]])

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

See the Enforcement table: APPCFG-1 to 3 are tool-enforced (ESLint, CI script); APPCFG-4 is review-only with CODEOWNERS approval by the frontend lead; APPCFG-5 and 6 are enforced by the deploy pipeline comparing image digests across environments.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

APPCFG-3 keeps secrets and internal hostnames out of the browser bundle; APPCFG-5 keeps region endpoints out of the image so a tenant's traffic cannot be pointed at another region's database by a build mistake. Secrets come only from the regional secrets manager ([[INF-secrets-and-keys]]).

<!-- check:exceptions -->
### Exceptions

Inline suppressions need a ticket ID and expiry under the repo-wide process ([[FND-governance]]); APPCFG-3 (no secrets in `NEXT_PUBLIC_`) and APPCFG-5 (no region endpoints in the image) are non-waivable.

<!-- check:ownership -->
### Ownership and change

Owner: frontend lead, with platform engineering for APPCFG-5 and APPCFG-6; changes to `next.config.ts` need CODEOWNERS approval from both; reviewed at each Next.js major upgrade.

<!-- end -->
