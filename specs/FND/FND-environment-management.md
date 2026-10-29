---
id: "FND-environment-management"
title: "Configuration and environment variables"
parent: "FND"
order: 3
type: "capability"
template: "standard"
status: "draft"
owner: null
indicative: false
summary: "Typed environment validation (Zod) at start-up; non-secret deployment configuration per environment and region; secrets only from the regional secrets manager; and the boundary with tenant and platform settings, feature flags and configuration packages"
links: []
rev: 4
syncHash: "e855737e1ebdb091"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 1.3 Configuration and environment variables

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Typed environment validation (Zod) at start-up; non-secret deployment configuration per environment and region; secrets only from the regional secrets manager; and the boundary with tenant and platform settings, feature flags and configuration packages

<!-- section:purpose -->
## Purpose and scope

Defines how **deployment configuration** reaches a running app or worker: one typed, validated schema per app in `@nomology/env`, non-secret values per environment and region from a parameter store, and secrets only from the regional secrets manager. A container whose configuration is invalid or incomplete refuses to start. Secret storage, KMS and rotation infrastructure are specified in [[INF-secrets-and-keys]]; the in-app secrets client is in [[PKG-encryption-utilities-key]].

This node also fixes the **boundary** between deployment configuration and the other kinds of configuration (rules ENV-11 to ENV-14):

| Kind | Varies by | Changed by | Lives in |
|---|---|---|---|
| Deployment configuration | Environment and region of the deployment | DevOps through Terraform and a deploy | This node |
| Secrets | Environment and region | DevOps and security, rotated | [[INF-secrets-and-keys]] |
| Release, operational and migration flags | Cohort, at run time | Engineering | [[PKG-feature-flags]] |
| Settings (product behaviour) | Platform, region, offering, tenant, unit, case type, case, user | Platform and tenant admins through change sets | [[PKG-settings]], [[PKG-configuration-scope-hierarchy]] |
| Tenant configuration artefacts and packages | Tenant | Tenant admins, implementation team | [[PKG-configuration-and-customisation]], [[PKG-configuration-packages]] |

Tenant-level settings (branding, limits, features) are never environment variables.

<!-- section:rules -->
## Rules

- **ENV-1** Every app (`web`, `worker-temporal`, `worker-jobs`, `doc-viewer`) defines its configuration as a Zod schema in `packages/env/src/<app>.ts` and loads it once at start-up through `loadEnv(schema)`. On failure the process logs the names (never values) of invalid variables and exits with code 78.
- **ENV-2** Only `@nomology/env` reads `process.env` (see [[FND-language-and-conventions]] CONV-6). Everything else imports the typed `env` object.
- **ENV-3** Server and browser variables are separate schemas. Browser-visible values use the `NEXT_PUBLIC_` prefix and are limited to values identical in every environment (for example the build ID). Values that differ by environment or region (API base URL, RUM collector endpoint) are sent to the browser at request time by the server, not inlined at build time.
- **ENV-4** Secrets (database passwords, Redis auth, provider API keys, signing keys, the payload codec key reference) are never committed, never baked into images, never passed as build arguments and never logged. They come from AWS Secrets Manager (or Azure Key Vault) in the same region as the workload, injected through the ECS task definition `secrets` field or the Container Apps secret reference, or fetched at runtime by the secrets client for rotating credentials.
- **ENV-5** Non-secret configuration per environment and region comes from AWS Systems Manager Parameter Store (or Azure App Configuration) under `/nomology/<env>/<region>/<app>/`. Committed defaults are allowed only for local development, in `packages/env/defaults/local.ts`.
- **ENV-6** Every schema includes `APP_ENV` (`local | dev | preview | staging | uat | prod`), `APP_REGION` (`in | sg | us`), `CLOUD` (`aws | azure`) and `RELEASE_ID`. Cross-field checks reject impossible combinations, for example a `prod` environment pointing at a non-prod database host or a Temporal namespace that does not match `<env>-<region>`.
- **ENV-7** Variable names are `UPPER_SNAKE_CASE`, grouped by prefix: `DATABASE_`, `REDIS_`, `TEMPORAL_`, `S3_` / `BLOB_`, `KMS_`, `OTEL_`, `AI_GATEWAY_`, `MAIL_`. Secrets end in `_SECRET`, `_PASSWORD`, `_KEY` or `_TOKEN` so scanners and the `NEXT_PUBLIC_` guard can spot them.
- **ENV-8** The app connects to Postgres only through PgBouncer (`DATABASE_URL`). The direct connection used by migrations (`DATABASE_MIGRATION_URL`) exists only in the migration task's schema, never in `web` or worker schemas ([[INF-separate-connection-settings-for]]).
- **ENV-9** `.env.example` lists every variable with a comment and no values. `.env*` files other than `.env.example` are git-ignored; local secrets are dummy values for local containers only.
- **ENV-10** A change that adds, renames or removes a variable updates the schema, `.env.example`, the parameter-store Terraform and the runbook in the same pull request. Renames follow expand and contract: the new name is read with fallback to the old for one release.
- **ENV-11** No environment variable or parameter may hold a tenant ID, tenant slug, unit, case type or any value that differs per tenant. Tenant-varying values are settings or configuration artefacts.
- **ENV-12** A value belongs here only if it describes the deployment (endpoints, account and resource names, pool sizes, timeouts, provider account IDs, sampling rates) or is needed before the database is reachable. Product behaviour that operators want to change at run time without a deploy, even if it is the same for every tenant (for example a maintenance banner, a regional default, a retention sweep window), is a `platform` or `region` scope setting changed through a platform change set ([[PKG-settings-platform-operations]], [[PKG-configuration-lifecycle]]).
- **ENV-13** No environment variable switches features on or off. Run-time on/off control of code paths uses [[PKG-feature-flags]]; build flags may not select region-specific code paths ([[DEP-environment-promotion-and-multi]], PROMO-10).
- **ENV-14** Configuration packages never contain environment configuration or secrets, and an environment's identity (`APP_ENV`, `APP_REGION`) decides which package signing keys it trusts ([[PKG-configuration-packages]]); unsigned packages are accepted only when `APP_ENV` is `local` or `dev` (`CONFIG_PACKAGES_ALLOW_UNSIGNED=true` is rejected by the schema in every other environment).

<!-- section:rationale -->
## Rationale

- **ENV-1** Failing at start-up turns a bad deploy into a failed health check during rollout ([[DEP-blue-green-canary-releases]]) instead of a runtime error during a hearing.
- **ENV-3** Next.js inlines `NEXT_PUBLIC_` values at build time. If they differed by environment we would need one build per environment, breaking build-once promotion ([[DEP-environment-promotion-and-multi]]).
- **ENV-4** Secrets in the same region keep credential material under the same residency and access controls as the data it protects.
- **ENV-6** Cross-field checks catch the most dangerous misconfiguration on a multi-region platform: an India container talking to a Singapore database.
- **ENV-8** Keeping the privileged migration connection out of app containers means a compromised web container cannot obtain the role described in [[MT-separate-privileged-role-used]].
- **ENV-11, ENV-12** Environment values change only with a deploy, have no per-tenant inheritance, no maker-checker, no history a tenant can see and no point-in-time answer. Product behaviour needs all of those, so it belongs in settings. The same split appears in low-code platforms that keep a definition in the deployable package and a value per environment (Power Platform environment variables [R1]); we keep only deployment facts in the environment.
- **ENV-13** Flags give per-cohort control, safe defaults and expiry; an environment variable gives none of those and needs a redeploy to undo.
- **ENV-14** Package trust must not depend on something an attacker could put in a package.

<!-- section:tooling -->
## Tooling and configuration

`packages/env` exports `loadEnv`, `webEnv`, `workerTemporalEnv`, `workerJobsEnv`, `migrateEnv`.

```ts
// packages/env/src/web.ts
import { z } from 'zod';
import { base } from './base';
export const webSchema = base.extend({
  DATABASE_URL: z.string().url().refine((u) => u.includes('pgbouncer'), 'ENV-8: must point at PgBouncer'),
  REDIS_URL: z.string().url(),
  TEMPORAL_ADDRESS: z.string(),
  TEMPORAL_NAMESPACE: z.string().regex(/^(local|dev|preview|staging|uat|prod)-(in|sg|us)$/),
  S3_DOCUMENTS_BUCKET: z.string(),
  SESSION_SIGNING_KEY: z.string().min(32),
  OTEL_EXPORTER_OTLP_ENDPOINT: z.string().url(),
}).superRefine((e, ctx) => {
  if (e.TEMPORAL_NAMESPACE !== `${e.APP_ENV}-${e.APP_REGION}`)
    ctx.addIssue({ code: 'custom', message: 'ENV-6: namespace must match env and region' });
});
export const env = loadEnv(webSchema);
```

Infrastructure: parameter paths and secret ARNs are created by Terraform in [[INF-cloud-and-iac]]; ECS task definitions reference them with `valueFrom`.

<!-- section:enforcement -->
## Enforcement

| Rule | Enforcement | Failure |
|---|---|---|
| ENV-1, ENV-6 | Start-up validation; container health check | Task exits 78, deployment circuit breaker rolls back |
| ENV-2 | ESLint CONV-6 | Lint error |
| ENV-3 | CI script scanning `NEXT_PUBLIC_*` names against ENV-7 secret suffixes and against a list of allowed public variables | Build fails |
| ENV-4, ENV-9 | gitleaks (pre-commit, CI), GitHub push protection, Trivy secret scan of built images | PR blocked; image not promoted |
| ENV-5 | Terraform owns parameter paths; review | |
| ENV-8 | Zod refinement; ESLint rule forbidding `DATABASE_MIGRATION_URL` outside `migrateEnv` | Start-up failure or lint error |
| ENV-10 | CI check that every schema key appears in `.env.example` and in the Terraform variable map | Build fails |
| ENV-11 | CI script rejecting parameter names or values matching UUIDs or tenant slugs from the tenant directory export; review | Build fails |
| ENV-12 | Review checklist item "deployment fact or product behaviour?"; `settings:registry-check` warns when a new env variable name matches an existing setting key | Review comment; CI warning |
| ENV-13 | ESLint rule forbidding `env.*_ENABLED` / `env.FEATURE_*` reads outside `packages/env` and infrastructure packages | Lint error |
| ENV-14 | Zod refinement on `CONFIG_PACKAGES_ALLOW_UNSIGNED` (allowed only for `local` and `dev`) | Start-up failure |

<!-- section:examples -->
## Examples

Good: an India production worker gets `APP_ENV=prod`, `APP_REGION=in`, `TEMPORAL_NAMESPACE=prod-in`, `DATABASE_URL` resolved from the India secrets manager at task start.

Good: the retention sweep window for India is changed by a platform change set on the region-scope setting `data.retention.sweep_window`, reviewed and audited, with no deploy.

Bad: `NEXT_PUBLIC_API_URL=https://api.in.example` set at build time, so the same image cannot be promoted to Singapore; or `DATABASE_URL` pasted into a GitHub Actions variable for a one-off script.

Bad: `TENANT_ACME_SSO_REQUIRED=true` in Parameter Store (a tenant setting in an environment variable, ENV-11), or `WHATSAPP_ENABLED=false` to switch a channel off in one region (use a flag or a region setting, ENV-13).

<!-- section:exceptions -->
## Exceptions

ENV-4 and ENV-8 are non-waivable. Other exceptions follow [[FND-governance#exceptions]].

<!-- section:questions -->
## Open questions

- [ ] Parameter Store vs AppConfig on AWS (AppConfig adds validation and staged rollout of config changes). With ENV-12 most run-time tunables move to platform settings, which reduces the need for AppConfig.
- [ ] Do runtime-fetched secrets (rotation without redeploy) apply to database credentials from Phase 1, or only to provider API keys?
- [ ] How is runtime public configuration delivered to statically rendered public pages ([[APP-public-and-sign-in-surfaces]])?
- [ ] Which existing environment variables are product behaviour and should become platform settings (inventory owed by DevOps and the configuration team)?

<!-- checks -->
## Template checks

<!-- check:enforcement -->
### Enforcement

Schema validation at start-up, lint for `process.env` and feature-style variables, a CI script for public variable names, `.env.example` completeness and tenant identifiers, gitleaks plus push protection, and Trivy secret scanning of images. Review-only items: ENV-5 parameter-path placement (covered by Terraform review) and the ENV-12 judgement, supported by a CI warning.

<!-- check:guardrails -->
### Security, tenancy and privacy guardrails

Secrets: ENV-4, ENV-7, ENV-9 and image secret scanning. Tenant isolation and least privilege: ENV-8 keeps the migration role out of app containers; ENV-11 keeps tenant data out of deployment configuration. Residency: ENV-6 rejects region mismatches between env, namespace and database host before the process serves traffic. Supply chain of configuration: ENV-14 ties package trust to the environment's identity.

<!-- check:compliance -->
### Compliance evidence

Supports ISO/IEC 27001:2022 Annex A controls on configuration management and on separation of development, test and production environments, and SOC 2 logical-access criteria. Evidence: Terraform plans for parameters and secrets, secrets-manager access logs, CI scan history.

<!-- check:ownership -->
### Ownership and change

Owner: DevOps lead with the information security owner as required reviewer for any change to ENV-4 or ENV-8.

<!-- citations -->
## Citations

```json
[
  {
    "id": "R1",
    "kind": "vendor",
    "title": "Microsoft Learn: Use environment variables in Power Platform solutions",
    "url": "https://learn.microsoft.com/en-us/power-apps/maker/data-platform/environmentvariables",
    "vendor": "Microsoft"
  }
]
```

<!-- end -->
