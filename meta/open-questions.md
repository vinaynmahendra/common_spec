# Open questions and assumptions

Generated from every spec's *Open questions* section by `python3 tools/specs.py index`. Answer them in the spec itself, then regenerate.

**1100 open items.**

## 1 Foundations and Repo

### 1.1 [Monorepo](../specs/FND/FND-monorepo.md)

- [ ] Remote cache: self-hosted (S3-backed, in our account) or Vercel Remote Cache? Decide by Phase 0 step 0b.
- [ ] Internal packages compiled to `dist/` (tsup) or consumed as TypeScript source (just-in-time) by Next.js and workers? Proposal: compiled for anything a worker imports.
- [ ] Does `infra/` (Terraform) live in this repo or a separate one with tighter access?
- [ ] Confirm Node.js and pnpm versions at Phase 0 kick-off.
- [ ] Is `apps/developer-portal` part of this repo or a separate static site repo?

### 1.2 [Language and conventions](../specs/FND/FND-language-and-conventions.md)

- [ ] UUIDv7 generated in the application, or database default? Depends on the Postgres version per region.
- [ ] Do we adopt `exactOptionalPropertyTypes`? It catches real bugs with Prisma optional fields but adds friction.
- [ ] Is commit signing (SSH or GPG) required on `main`, or is GitHub's verified squash commit enough for audit?

### 1.3 [Configuration and environment variables](../specs/FND/FND-environment-management.md)

- [ ] Parameter Store vs AppConfig on AWS (AppConfig adds validation and staged rollout of config changes). With ENV-12 most run-time tunables move to platform settings, which reduces the need for AppConfig.
- [ ] Do runtime-fetched secrets (rotation without redeploy) apply to database credentials from Phase 1, or only to provider API keys?
- [ ] How is runtime public configuration delivered to statically rendered public pages ([[APP-public-and-sign-in-surfaces]])?
- [ ] Which existing environment variables are product behaviour and should become platform settings (inventory owed by DevOps and the configuration team)?

### 1.4 [Environments](../specs/FND/FND-environments.md)

- [ ] Which non-prod AWS region hosts dev and preview? (Synthetic data only, so cost and latency decide.)
- [ ] Do we need a separate performance-test environment or is staging sized up during load tests ([[TST-performance-and-load-testing]])?
- [ ] Confirm ENVS-5 with legal: is a client's written confirmation enough for UAT, or must client UAT always be a sandbox tenant in production?
- [ ] Is a UAT environment per region needed from Phase 3, or only when the first client acceptance starts?

### 1.5 [Governance](../specs/FND/FND-governance.md)

- [ ] Is the spec workspace or the repository the source of truth for ADRs? Proposal: spec workspace, with the repo index generated from it.
- [ ] Confirm team names and membership for CODEOWNERS.
- [ ] Are two approvals required for all `prisma/migrations/**` changes or only contract-phase migrations?
- [ ] Should client-driven requirements (for example a client contract clause) be recorded as ADR context with the contract reference, given contract confidentiality?

## 2 Next.js App

### 2.1 [App configuration](../specs/APP/APP-app-configuration.md)

- [ ] Do Azure Container Apps deployments need any build-time difference (for example image registry or base image), or can APPCFG-5 hold there too? (owner: platform engineering)
- [ ] Should UAT run the production image with production-like region config per client, or a shared UAT per region? (owner: DevOps, see [[FND-environments]])

### 2.1.1 [App Router, next.config, middleware](../specs/APP/APP-app-router-next-config.md)

- [ ] Tenant directory cache TTL in `proxy.ts` (60 s proposed): acceptable delay for suspension to take effect, or do we need push invalidation? (owner: platform engineering, [[MT-tenant-resolution]])
- [ ] Which OpenTelemetry package: `@vercel/otel` or the plain OTel Node SDK, given self-hosting? (owner: observability)
- [ ] Is `experimental.sri` (needed for hash-based CSP on static shells) supported with the bundler we build with? (owner: frontend lead, [[APP-rendering-and-caching-strategy]])

### 2.1.2 [Route groups per persona](../specs/APP/APP-route-groups-per-persona.md)

- [ ] Should `(platform-admin)` move to a separate Next.js app and image so it can be deployed only inside the private network? (owner: security lead; Decision record needed)
- [ ] Confirm URL prefixes with product, especially whether SEBI ODR investor journeys need a simpler prefix than `/portal` (owner: product, CORD)
- [ ] Confirm proposed session timeouts with security and with institution tenants that have their own policies (owner: security, [[PKG-mfa-session-management-device]])
- [ ] Do transcribers who work for several tenants need a cross-tenant work queue, which would conflict with tenant-per-host? (owner: TERES product, [[DOM-transcribers]])

### 2.1.2.1 [Party and counsel portal](../specs/APP/APP-party-and-counsel-portal.md)

- [ ] Upload limits (500 MB per file, 2 GB per filing) and whether tenants can raise them (owner: product, [[DOM-documents]])
- [ ] Should party-to-party contact details ever be shown in the portal, or only through served documents? (owner: legal, per tenant rules)
- [ ] Payment gateway per billing entity and region, and whether any embeds a widget (owner: finance, [[BIL-payment-gateway-integration]])
- [ ] Is a "shared device" option enough for court-kiosk use, or do some tenants need a kiosk mode? (owner: CORD product)

### 2.1.2.1.1 [Hearing room (in-browser)](../specs/APP/APP-hearing-room-in-browser.md)

- [ ] Video provider per region, and whether it is an SDK in our page or an iframe embed; drives Permissions-Policy and CSP (owner: TERES product, [[INT-video-conferencing-for-hearings]])
- [ ] Join window (30 minutes before start) and whether witnesses join through the counsel portal or a separate guest link (owner: product with institution tenants)
- [ ] Are party breakout rooms required by any tenant's procedure, and must they be excluded from recording? (owner: legal)
- [ ] Phone dial-in availability per region (owner: TERES product)

### 2.1.2.2 [Neutral workspace](../specs/APP/APP-neutral-workspace.md)

- [ ] Rich-text editor choice (ProseMirror-based such as Tiptap, or Lexical) judged on screen-reader support and structured output (owner: frontend lead; Decision record)
- [ ] Is single-editor locking acceptable to three-member tribunals, or is real-time co-editing needed? (owner: TERES product with HKIAC CMP)
- [ ] Can tribunal secretaries see deliberations at tenants where they assist the tribunal? Varies by institutional rules (owner: legal)
- [ ] Which AI drafting features are allowed per tenant, given ISO 42001 impact assessments ([[AI-ai-governance-and-impact]])

### 2.1.2.3 [Secretariat console](../specs/APP/APP-secretariat-console.md)

- [ ] Bulk limits (500 explicit IDs, 10,000 by filter) and whether SEBI ODR tenants need more (owner: CORD product)
- [ ] Should queue counts update live (server-sent events) or is 30-second freshness enough? (owner: frontend lead)
- [ ] Keyboard shortcut set for the console and how users change it (owner: UX)

### 2.1.2.4 [Transcriber workspace](../specs/APP/APP-transcriber-workspace.md)

- [ ] Play and seek shortcuts that do not clash with screen-reader keys (proposed: Ctrl+Space play/pause, Ctrl+, and Ctrl+. seek 5 s), and whether users can remap them (owner: UX)
- [ ] Is a visible watermark required by tenants, and is it acceptable for transcribers with low vision? (owner: product, security)
- [ ] Do external vendor transcribers sign in through the tenant host, or through a vendor host spanning tenants? (owner: TERES product)

### 2.1.2.5 [Tenant admin console](../specs/APP/APP-tenant-admin-console.md)

- [ ] Which configuration areas need maker-checker by default per tenant type? Proposed defaults are in [[PKG-separation-of-duties]] and the `PKG-settings-*` catalogues; product to confirm with institution tenants. (owner: product)
- [ ] Should reports be embedded here or in a separate reporting surface ([[RPT-report-infrastructure]])? Proposed: admin reports (seats, adoption, configuration health) here; operational case reports in the reporting surface. (owner: reporting lead)
- [ ] Hindi console UI at launch or later? (owner: product, CORD)
- [ ] Should a `tenant_owner` be able to see a read-only "configuration health score" comparing their settings with blueprint recommendations? (owner: product)

### 2.1.2.5.1 [Admin audit log, change history and rollback](../specs/APP/APP-admin-change-history.md)

- [ ] Should tenants be able to receive a monthly signed digest of their audit anchor ([[PKG-audit-trail#questions]]) from this page? (owner: product)

### 2.1.2.5.2 [Admin copilot](../specs/APP/APP-admin-copilot.md)

- [ ] Should platform admins get the same copilot in `/platform/...` over the platform internal API, and with which extra limits (cross-tenant reads)? (owner: admin group, platform security)
- [ ] Default conversation retention (proposed 90 days). (owner: legal)
- [ ] Should tenants be allowed to add their own copilot instructions (for example naming conventions)? Proposed: not at launch. (owner: product)
- [ ] Does the change-set API (`/admin/v1/change-sets`, decision D3) support every admin domain at launch, including direct operations recorded as `admin.op` items, or do some domains need console-only edits first? (owner: config and admin groups)

### 2.1.2.5.3 [Bulk administration, import and export](../specs/APP/APP-bulk-admin-operations.md)

- [ ] Is 10,000 rows per file the right default for SEBI ODR institutions, or should their blueprint default be 50,000? (product, CORD)
- [ ] Should bulk party creation (outside admin, for case intake) reuse this pipeline or stay in [[INT-aggregator-intake-api]]? Proposed: stay separate; share the parser and validation library. (platform core)
- [ ] Approval threshold defaults (50 step-up, 500 maker-checker): confirm with institution tenants. (security)
- [ ] XLSX support in v1 or CSV only? (product)

### 2.1.2.5.4 [User, group and access administration](../specs/APP/APP-user-and-access-admin.md)

- [ ] Groups as a first-class authorization subject: confirm with the authz group that role assignments to groups are in [[PKG-authorization-data-model]]. (owner: authz group)
- [ ] Should access reviews be required by default for admin roles (quarterly) or only offered? Proposed: on by default for `tenant_owner`, `tenant_admin`, `security_admin`; tenant may switch off with a reason. (owner: security, [[SEC-access-reviews]])
- [ ] Should party memberships created by intake appear in the users list at all, or in a separate "Parties" view? Proposed: separate filter, hidden by default. (owner: product, CORD)

### 2.1.2.6 [Platform admin and support console](../specs/APP/APP-platform-admin-and-support.md)

- [ ] Separate app and image for `(platform-admin)` so it can run only on private networking? (owner: security lead; Decision record needed)
- [ ] Is "view as" read-only always, or can support act with tenant approval (for example to fix a stuck filing)? Proposed in [[PKG-support-access-and-impersonation]]: read-only in v1; writes only through `config_write` grants. (owner: security with tenants)
- [ ] Should the route-group table in [[APP-route-groups-per-persona]] be updated from `/ops` to `/platform`? Proposed yes. (owner: frontend lead)

### 2.1.2.6.1 [Tenant provisioning and onboarding wizard](../specs/APP/APP-tenant-onboarding-wizard.md)

- [ ] Should a tenant owner be able to self-serve a sandbox from `/admin/sandboxes`, or only through the wizard and platform admins? (owner: product, with [[PKG-settings-billing-and-plans]])
- [ ] Which checklist items are mandatory before the first case can be created (for example "second owner added", "data processing terms accepted")? (owner: product with legal)
- [ ] Do court or government programmes need a separate approval step (for example a signed order or MoU reference) before provisioning? (owner: account management)

### 2.1.2.7 [Public and sign-in surfaces](../specs/APP/APP-public-and-sign-in-surfaces.md)

- [ ] Bot protection provider (if any) and its accessibility and residency (owner: security)
- [ ] Invitation expiry (7 days proposed) and whether institutions can change it (owner: product)
- [ ] Should public filing be available for all tenant types or only CORD and SEBI ODR tenants? (owner: CORD product)

### 2.1.2.8 [Administration model and admin personas](../specs/APP/APP-administration-model.md)

- [ ] Should `tenant_owner` be held by a named individual at the institution (contractual signatory) or by any person the institution chooses? (owner: legal and account management)
- [ ] Minimum number of `tenant_owner`s: one (proposed, with a warning) or two (stricter, but hard for small CORD tenants)? (owner: product)
- [ ] Do unit admins need to administer unit-level settings for notification policies and AI policy, or only users and calendars in v1? (owner: product with SEBI ODR institution tenants)
- [ ] Should `auditor` be allowed to see support-session activity details, or only counts? Proposed: details. (owner: security)
- [ ] Shared model naming: the route group table in [[APP-route-groups-per-persona]] still shows the platform console at `/ops`; this node uses `/platform` per the shared model. The route-group owner should update its table. (owner: frontend lead)
- [ ] Is "may assign" for `user_admin` limited to roles with no admin permission at all, or to roles whose permissions are a subset of its own (proposed: both conditions)? (owner: security, with [[PKG-roles-and-permission-sets]])

### 2.1.3 [Security headers, CSP, CORS](../specs/APP/APP-security-headers-csp-cors.md)

- [ ] Is Trusted Types (`require-trusted-types-for 'script'`) feasible with our dependencies? Trial in Report-Only (owner: security)
- [ ] HSTS `preload` for tenant custom domains: offer as opt-in or never? (owner: DevOps)
- [ ] Do any IdPs used by tenants require pop-up SSO, needing `same-origin-allow-popups` on sign-in? (owner: identity, [[PKG-sso-saml-oidc-per-tenant]])

### 2.1.4 [Rendering and caching strategy](../specs/APP/APP-rendering-and-caching-strategy.md)

- [ ] Is Next.js build-time SRI (`experimental.sri`) available with our bundler for the hash-based CSP on `(public)`? If not, use nonce CSP for public pages too. (owner: frontend lead)
- [ ] Redis: separate logical DB on the shared regional Redis, or a dedicated cache cluster? (owner: platform engineering, [[INF-redis]])
- [ ] Should any authenticated list (for example the secretariat queue counts) use `'use cache: private'` to speed up back navigation? (owner: frontend lead)
- [ ] Record the rendering-mode decision as an ADR under [[ADR]] once reviewed.

### 2.2 [Framework dependencies](../specs/APP/APP-framework-dependencies.md)

- [ ] Merged from "ORM": Prisma, validation (Zod), data fetching (TanStack Query), forms (React Hook Form) — now folded into DEP-1; confirm and close.
- [ ] Choice of i18n library and date library (owners: [[I18N-i18n]], [[I18N-l10n]])
- [ ] Renovate or Dependabot (owner: DevOps)

### 2.3 [API layer](../specs/APP/APP-api-layer.md)

- [ ] Confirm that the public REST router lives in `apps/web` rather than a separate API service per region (owner: platform architecture)

### 2.3.1 [API style (internal and external)](../specs/APP/APP-route-handlers-trpc-for-internal.md)

- [ ] Public REST router: Hono or ts-rest (owner: platform architecture; Decision record)
- [ ] Should the public API be served from the same containers as the web app, or a separate service in each region for independent scaling? (owner: platform architecture)

### 2.3.1.1 [Internal API — tRPC routers per persona](../specs/APP/APP-internal-api-trpc-routers-per.md)

- [ ] Split this node into one child per persona router at Phase 4 (owner: platform architecture)
- [ ] Should `common.search` be tRPC or a Route Handler with streaming results? (owner: search lead, [[PKG-search]])

### 2.3.2 [API versioning, rate limiting, idempotency keys](../specs/APP/APP-api-versioning-rate-limiting.md)

- [ ] Confirm deprecation notice periods against client contracts (HKIAC CMP, MII integrations) (owner: legal and product)
- [ ] Should the `RateLimit` headers follow the current IETF draft names, given the draft may change? (owner: platform architecture)
- [ ] Rate-limit numbers per class need validation by load test and by aggregator expectations ([[INT-aggregator-intake-api]])

### 2.3.3 [Server Actions and mutation conventions](../specs/APP/APP-server-actions-and-mutation.md)

- [ ] Should `defineAction` support optimistic UI helpers (`useOptimistic`) as standard, or leave per screen? (owner: frontend lead)
- [ ] How long to keep idempotency records for Server Actions (24 hours proposed, same as API) (owner: platform architecture)

### 2.3.4 [API error catalogue (problem types)](../specs/APP/APP-api-error-catalogue-problem.md)

- [ ] Developer portal domain for type URIs (owner: product, [[DOC-api-documentation-openapi]])
- [ ] Should `detail` be localised for public API callers (via `Accept-Language`) or English only? (owner: content, [[DOC-developer-facing-api-copy]])

### 2.4 [Frontend standards](../specs/APP/APP-frontend-standards.md)

- [ ] Who owns visual regression across tenant themes (proposed: design-system team with [[TST-accessibility-testing]])?

### 2.4.1 [Accessibility (WCAG 2.2 AA)](../specs/APP/APP-accessibility-wcag-2-1-aa.md)

- [ ] Legal confirmation of the instruments and standards in the obligations summary, especially the RPwD Rules standard by reference and the SEBI circular's reach to ODR institutions (owner: legal)
- [ ] Separate criteria mappings for `(transcriber)`, `(tenant-admin)` and `(platform-admin)` (owner: accessibility lead)
- [ ] Who is the accessibility lead and ACR signatory? (owner: CTO)
- [ ] Is IS 17802 the right Indian reference for documents and real-time communication clauses? (owner: legal / accessibility lead)
- [ ] Rename node ID to reflect WCAG 2.2 (owner: workspace admin)

### 2.4.1.1 [Accessibility legal obligations register](../specs/APP/APP-accessibility-legal-obligations.md)

- [ ] Legal to confirm every row, especially L1 standard by reference, L3 reach to ODR institutions empanelled with MIIs, and L6 compliance dates (owner: legal)
- [ ] Does any tenant contract set a stricter target or shorter remediation times than our standard? (owner: legal, account managers)
- [ ] Who watches for final versions of draft instruments (L2) and EN 301 549 updates? (owner: accessibility lead)
- [ ] Does HKIAC CMP's contract contain accessibility obligations? (owner: TERES account lead)
- [ ] Do we need a Singapore-specific review (owner: TAPL legal)

### 2.4.1.2 [Accessibility Conformance Reports and accessibility statements](../specs/APP/APP-accessibility-conformance.md)

- [ ] Machine-readable format: OpenACR or another (owner: accessibility lead)
- [ ] Separate ACRs per product (CORD, TERES, HKIAC CMP) or one platform ACR with product scope notes? (owner: product)
- [ ] Independent auditor for the first ACR, and for SEBI-regulated tenants annually? (owner: CTO, budget)

### 2.4.1.3 [Party and counsel portal accessibility conformance](../specs/APP/APP-party-and-counsel-portal-2.md)

- [ ] Which Indian languages are needed at launch for SEBI ODR tenants, and are screen readers tested in them (owner: CORD product)
- [ ] Do we need an assisted-filing route by phone for parties who cannot use the portal (owner: CORD operations)

### 2.4.1.4 [Secretariat console and neutral workspace accessibility conformance](../specs/APP/APP-secretariat-console-and-neutral.md)

- [ ] Editor library decision with screen-reader evaluation (owner: frontend lead)
- [ ] Which JAWS versions do institution IT departments deploy (owner: account managers to survey)
- [ ] Console keyboard shortcut set (owner: UX)

### 2.4.1.5 [Accessibility feedback, accommodation and grievance](../specs/APP/APP-accessibility-feedback.md)

- [ ] Grievance response periods required by SEBI-regulated tenants or by law (owner: legal)
- [ ] Is the requester's disability information ever needed? Proposed: never required; if volunteered, stored as sensitive personal data with case-level restriction (owner: privacy)
- [ ] Who remediates inaccessible documents uploaded by another party: the platform (OCR, conversion) or the filing party on direction of the tribunal? (owner: legal with institutions)

### 2.4.2 [Responsive / mobile-first](../specs/APP/APP-responsive-mobile-first.md)

- [ ] Confirm the reduced phone view scope for `(secretariat)` and `(neutral)`: read-only or limited actions? (owner: UX)

### 2.4.3 [Error boundaries, loading and empty states](../specs/APP/APP-error-boundaries-loading-and.md)

- [ ] Should offline mutation queuing exist anywhere beyond uploads and drafts? (owner: frontend lead)
- [ ] Alert threshold for boundary hits (0.5% proposed) (owner: observability)

### 2.4.3.1 [Error message catalogue](../specs/APP/APP-error-message-catalogue.md)

- [ ] Legal approval of the deadline-related messages (owner: legal)
- [ ] Which codes tenants may override (proposed: filing and payment messages only) (owner: product)
- [ ] Support contact shown in messages: tenant's or Nomology's? Proposed: tenant's for case matters, Nomology's for technical faults (owner: operations)

### 2.4.4 [Document viewer and sandbox origin](../specs/APP/APP-document-viewer-and-sandbox.md)

- [ ] Sandbox registrable domain per region, and whether Azure deployments use a separate one (owner: DevOps)
- [ ] Are shared annotations needed between co-counsel, or private only at first? (owner: product)
- [ ] Commercial PDF engine (better accessibility and redaction) versus PDF.js (owner: frontend lead; Decision record)

### 2.4.5 [Frontend performance budgets](../specs/APP/APP-frontend-performance-budgets.md)

- [ ] Confirm device profiles with RUM data after the first pilot tenant (owner: frontend lead)
- [ ] Should budgets differ for Azure deployments? Proposed: no (owner: DevOps)

### 2.4.6 [Client state and data-fetching conventions](../specs/APP/APP-client-state-and-data-fetching.md)

- [ ] Do we need encryption of IndexedDB drafts with a per-session key (WebCrypto), for shared devices? (owner: security)
- [ ] URL state library choice (owner: frontend lead)

### 2.4.7 [Voice, tone and content style guide](../specs/APP/APP-voice-tone-and-content-style.md)

- [ ] Spelling standard: British English (proposed, consistent with Indian and Singapore usage) or US English for US tenants (owner: content lead)
- [ ] Should neutrals' role names be tenant-configurable (for example "Sole Arbitrator" vs "Arbitrator") (owner: product)
- [ ] Who approves tenant overrides that change procedural meaning (owner: legal with the tenant)

## 3 Multi-tenancy (Core)

### 3.1 [Tenant model](../specs/MT/MT-tenant-model.md)

- [ ] Assumption: the CORD tenant's home region is India. To be confirmed.
- [ ] Should a suspended tenant still send legally required notices on running cases (for example service of an award)? Proposed: yes, configurable per tenant type; legal to confirm.
- [ ] One account per region (TM-R3) versus a global identity index: decision needed (see [[MT-data-residency-2]]).
- [ ] Are custom roles a plan feature or available to all tenants?
- [ ] Inactive account deletion period (24 months proposed) to be confirmed by legal and the DPO.

### 3.1.1 [Tenancy and identity schema](../specs/MT/MT-tenancy-and-identity-schema.md)

- [ ] Global identity index versus one account per region (owner: CTO, with legal).
- [ ] Should party accounts created by aggregator bulk intake be full user accounts or lightweight "contact" records until the party first signs in? Affects volume and consent.
- [ ] Per-tenant data keys (`data_key_ref`) pending ADR.
- [ ] Inactive-account anonymisation period (24 months proposed), owner: DPO.
- [ ] Confirm one Postgres schema (`public`) per regional database versus a schema per bounded context.
- [ ] Keep the physical table name `org_unit` for the shared-model `unit` scope, or rename it to `unit`? Proposed: keep, and say so in every node that uses `unit_id`. (owner: platform lead)
- [ ] How do `tenant_type` selectors on platform, region and offering values resolve for a `sandbox` tenant? Assumption: with the parent's type. (owner: configuration lead, [[PKG-configuration-scope-hierarchy]])
- [ ] What does `customer_account_id` point to: a billing customer record in [[BIL-plans-entitlements-and-usage]] or a new platform-level `customer_account` table? (owner: CTO with billing)
- [ ] Backfill rule for `membership.kind` of neutrals: panel neutrals who are not staff should be `external`; confirm with institutions. (owner: product)

### 3.2 [Tenant resolution](../specs/MT/MT-tenant-resolution.md)

- [ ] Product domains and regional host naming (for example `{slug}.{product-domain}` with regional CNAMEs) to be confirmed by DevOps.
- [ ] Wrong-region requests: redirect at CDN by host (preferred) or in middleware only?
- [ ] Do custom domains need to be supported in Phase 1 for institutional tenants?
- [ ] Should the aggregator credential name the tenant per call (proposed) or be issued per tenant?

### 3.3 [Isolation strategy](../specs/MT/MT-isolation-strategy.md)

- [ ] Confirm the exact ASVS 5.0.0 requirement IDs for the mapping table.
- [ ] Should `SECURITY DEFINER` functions be banned outright on tenant tables, or allowed via a register? Proposed: register with security sign-off.
- [ ] Is a tenant-level restore (one tenant to a point in time) a contractual promise for any institutional tenant? It changes the backup design.
- [ ] Do any clients require a dedicated (silo) database? If so, record as a separate ADR rather than a tenancy mode.
- [ ] Which statement-logging approach for `nomo_platform_ops` (pgaudit on managed Postgres in each region, or application-level logging only)?

### 3.3.1 [Tenant ID on every tenant table](../specs/MT/MT-every-tenant-owned-table-carries.md)

- [ ] Should high-volume tables (audit events, notification deliveries) be list- or hash-partitioned by `tenant_id` to make tenant deletion cheap? Owner: [[PKG-audit-log-schema]] and [[INF-database]].

### 3.3.2 [Platform-level tables](../specs/MT/MT-platform-level-tables.md)

- [ ] Do reference tables that tenants can extend (for example tenant-specific holiday calendars) need a split into a platform part and a tenant-owned part? Proposed: yes, `holiday_calendar` (platform) plus `tenant_holiday` (tenant-owned), see [[PKG-calendars-and-deadline]].

### 3.3.3 [Forced RLS on tenant tables](../specs/MT/MT-rls-enabled-and-forced-on.md)

- [ ] Should `app.current_tenant_id()` raise an error instead of returning NULL when context is missing, to make bugs louder? Proposed: no (fail closed quietly in SQL; the package raises the error before the query).

### 3.3.4 [Prisma implementation](../specs/MT/MT-prisma-implementation.md)

- [ ] Interactive transactions for every call add round trips; is a batch-transaction mode (`$transaction([setConfig, query])`) worth offering for single-query reads? Proposed: no, keep one code path until measurements say otherwise.
- [ ] Confirm `pgbouncer=true` behaviour with the Prisma version chosen in [[APP-framework-dependencies]] (prepared statements support in PgBouncer 1.21+ may allow turning it off).
- [ ] Is RDS Proxy in scope for any region? If so it must pass the leak test above ([[INF-pgbouncer]]).

### 3.3.4.1 [Transaction-scoped tenant context](../specs/MT/MT-prisma-client-extension-wraps.md)

- [ ] Folded from the merged item "Tenant context set per transaction only": now part of the statement above. Remove the merged note once reviewed.
- [ ] Should nested `withTenant` calls join the outer transaction (proposed) or be rejected?

### 3.3.4.2 [Non-owner application role](../specs/MT/MT-app-connects-as-a-non.md)

- [ ] On Azure Database for PostgreSQL Flexible Server, confirm which built-in roles the administrator account grants and that `nomo_app` inherits none of them.

### 3.3.4.3 [Privileged migration role](../specs/MT/MT-separate-privileged-role-used.md)

- [ ] Should `nomo_platform_ops` be split further (for example a delete-only role for offboarding)?
- [ ] Maximum credential lifetime for platform-ops jobs: 4 hours proposed.

### 3.3.4.4 [RLS policies in migrations](../specs/MT/MT-prisma-migrations-include-rls.md)

- [ ] Should policies be declared once in a YAML/TS manifest and rendered into migrations (less hand-written SQL), or stay hand-written with lint (proposed for Phase 1)?

### 3.3.5 [Safeguards](../specs/MT/MT-safeguards.md)

- [ ] Add a fourth safeguard for noisy-neighbour fairness (per-tenant rate limits and queue fairness)? Proposed: yes, as a requirement here.
- [ ] Retention period for CI evidence (13 months proposed, to cover a SOC 2 Type II period plus margin).

### 3.3.5.1 [Cross-tenant isolation tests](../specs/MT/MT-automated-tests-that-prove-one.md)

- [ ] Should the nightly run also execute against a production-like anonymised dataset in staging (larger, realistic volumes)? Proposed: yes, in Phase 3.

### 3.3.5.2 [RLS check for new tables](../specs/MT/MT-lint-review-check-that-every.md)

- [ ] Build the SQL lint in-house (parser such as `pgsql-ast-parser`) or apply migrations to a scratch database and inspect the catalogue only? Proposed: both; the catalogue check is authoritative, the parser gives earlier, clearer messages.

### 3.3.5.3 [Cross-tenant reporting role](../specs/MT/MT-cross-tenant-reporting-via-a.md)

- [ ] Minimum cohort size for external aggregates (5 proposed); owner: CCO with legal.
- [ ] Warehouse technology per region (Postgres replica only in Phase 7, or a columnar store) — see [[RPT-report-infrastructure]].

### 3.4 [Data residency](../specs/MT/MT-data-residency-2.md)

- [ ] Which cloud regions per country (for example AWS Mumbai / Hyderabad for India, Singapore, a US region) and whether DR uses a second in-country region. Owner: DevOps with CTO.
- [ ] Where is the directory's primary hosted, and is an institution's name and domain acceptable as global data? Assumption: not personal data; to be confirmed by legal.
- [ ] Global identity index: needed, and if so, where may it live? Owner: CTO with legal.
- [ ] Which client contracts require Azure, and in which regions? Each becomes its own region code.
- [ ] AI model endpoints per region and the tenant opt-out default for out-of-region AI processing. Owner: [[AI-ai-gateway]].
- [ ] Merged item "one shared database per region; tenants pinned to their region's database" has been folded into the design above; remove after review.

### 3.5 [Tenant lifecycle](../specs/MT/MT-tenant-lifecycle.md)

- [ ] Per-tenant KMS keys and crypto-shredding: confirm with DevOps cost and key limits per region; record as ADR.
- [ ] Default export window and deletion deadline (30 and 90 days proposed) to be confirmed against standard client contracts.
- [ ] Export format: JSON Lines + documents + configuration package is proposed; do institutions need a case-file format (for example per-case folders with PDFs) instead?
- [ ] What must Nomology keep after deletion (for example invoices for tax law, audit records of the offboarding itself)? To be confirmed by finance and legal.
- [ ] During suspension for non-payment, which legally required notices still go out? Legal to decide per tenant type; the switch is `platform.lifecycle.suspension_legal_notices_continue`.
- [ ] Should tenant owners be able to request offboarding themselves from the console (with platform confirmation), or only through the account manager? (owner: product with legal)

## 4 Localization and Internationalization

### 4.1 [i18n](../specs/I18N/I18N-i18n.md)

- [ ] Confirm `next-intl` vs FormatJS `react-intl` by ADR.
- [ ] TMS vendor and where it hosts data.
- [ ] Which locales need RTL at launch, if any? (Urdu for India party journeys is a candidate.)
- [ ] Do SMS templates registered on India's DLT platform need per-language registration, and how does that limit tenant overrides ([[PKG-notification-copy]])?

### 4.2 [l10n](../specs/I18N/I18N-l10n.md)

- [ ] Launch locales per tenant (for example `en-IN`, `hi-IN`, `en-SG`, `en-US`; `zh-Hant-HK` and `zh-Hans` only if a tenant needs them).
- [ ] Should the time zone abbreviation be replaced by UTC offset where abbreviations are ambiguous (for example "IST")? Proposal: show both, "IST (UTC+05:30)", on legal deadlines.
- [ ] Node.js full ICU in all images and in Azure deployments: confirm.

### 4.3 [Content](../specs/I18N/I18N-content.md)

- [ ] Boundary with [[PKG-document-and-notification]]: who owns template authoring UI and approval? Proposal: that package owns authoring; this package owns storage and resolution of locale and jurisdiction variants.
- [ ] Do jurisdiction variants key on seat, governing law or tenant only?
- [ ] Should tenant packs sync to the TMS for translation, or are tenant overrides written directly per locale?

### 4.3.1 [Legal, declaration and consent text register](../specs/I18N/I18N-legal-declaration-and-consent.md)

- [ ] Legal to confirm the owner and approver for each row, per region and contracting entity.
- [ ] Which texts need re-acceptance on change, and what counts as a material change?
- [ ] Is the authoritative language always English, or may a tenant's rules make another language authoritative?
- [ ] Is click-acceptance sufficient for declarations under each institution's rules, or is e-signature required for some (for example the neutral's declaration)?

### 4.4 [Platform glossary and terminology governance](../specs/I18N/I18N-platform-glossary-and.md)

- [ ] Confirm defined terms used by each launch tenant's rules (for example a SEBI ODR institution's own terms for the parties), with legal.
- [ ] Is "neutral" acceptable to parties anywhere, or staff and API only? Proposal: staff and API only.
- [ ] Which locales get the termbase first?

## 5 Platform Packages (shared libraries)

### 5.1 [Authentication](../specs/PKG/PKG-authentication.md)

- [ ] Build vs self-host: in-house package on vetted libraries (for example `openid-client` for OIDC, a SAML library, `@simplewebauthn/server`) vs a self-hosted identity server per region. A hosted global IdP is ruled out unless it offers in-region data storage for India, Singapore and US. Owner: CTO; record as an ADR.
- [ ] Do SEBI ODR tenants require identity assurance for investors beyond email or mobile control? Assumption: email or mobile OTP is sufficient; to be confirmed by legal (tracked in [[PKG-external-party-identity#questions]]).
- [ ] Should counsel identities be shareable across regions with consent (one login, two regional records) or kept fully separate? Owner: product and DPO.
- [ ] Should `acr` values be exposed to tenants' own systems in webhook payloads or the admin API for their audits? Owner: product.
- [ ] Social IdPs for counsel (not only parties) — demand and risk? Owner: product and security.

### 5.1.1 [Email/password, magic link, OTP](../specs/PKG/PKG-email-password-magic-link-otp.md)

- [ ] Breached-password check: external k-anonymity service (data leaves region as a 5-character hash prefix) or offline corpus per region? Owner: security.
- [ ] Is SMS OTP needed outside India at launch? Affects SMS provider choice per region in [[INT-messaging-providers]]. Owner: product.
- [ ] WhatsApp OTP for parties in India — acceptable as first factor, and under which provider terms? Owner: product, security, legal.

### 5.1.2 [SSO (SAML, OIDC) per tenant](../specs/PKG/PKG-sso-saml-oidc-per-tenant.md)

- [ ] SAML library choice and whether to run a self-hosted SAML-to-OIDC bridge per region instead of parsing SAML in the app. Owner: security.
- [ ] Do neutrals sign in through an institution's IdP (institution-managed accounts) or their own? Affects linking across tenants. Owner: product.
- [ ] Should law-firm connections be shareable across tenants of the same region (configured once) or always per tenant? Proposed: per tenant for isolation; revisit with demand. Owner: product, security.
- [ ] Which social providers per offering and region at launch (LinkedIn for counsel?). Owner: product.
- [ ] Singpass relying-party onboarding: does Nomology (TAPL) onboard once for all Singapore tenants, or does each tenant onboard? Owner: legal, TAPL operations.
- [ ] Is there an Indian government sign-in scheme suitable for private-sector relying parties (for example via DigiLocker sign-in) that we should support? Assumption: not at launch. Owner: legal, product.

### 5.1.2.1 [Domain verification and home-realm discovery](../specs/PKG/PKG-domain-verification.md)

- [ ] Which public and disposable email domain list do we use, and who maintains it per region? (Security)
- [ ] Should HTTP file verification (`/.well-known/nomology-verification.txt`) be offered as an alternative to DNS for tenants that cannot change DNS quickly? (Product, Security)
- [ ] Should the TXT record name be `_nomology-challenge` on the domain apex, or support delegated verification through a CNAME? (Engineering)
- [ ] Do Indian government `gov.in` / `nic.in` subdomains need a standard manual verification path agreed with NIC? (Legal, Operations)

### 5.1.3 [MFA, session management, device management](../specs/PKG/PKG-mfa-session-management-device.md)

- [ ] Is identity re-proof for assisted MFA reset a tenant process (secretariat verifies the neutral by video) or a Nomology support service for small tenants? Owner: operations.
- [ ] Should the platform offer WebAuthn related origins so one passkey works across a tenant's several custom hostnames? Proposed: no in phase 1. Owner: security.
- [ ] AAGUID metadata: use the FIDO Metadata Service to show authenticator names and certification levels? Owner: security.

### 5.1.4 [Accessible authentication and identity / KYC alternatives](../specs/PKG/PKG-accessible-authentication-and.md)

- [ ] Legal to confirm the exact Pragya Prasun directions that apply to our KYC and identity verification journeys and which tenants they cover (owner: legal).
- [ ] Choose the KYC provider per region and confirm it supports a non-liveness alternative route (owner: integrations lead).
- [ ] Confirm the accessibility of Singpass and DigiLocker consent screens with their published conformance information before enabling them (owner: accessibility lead).
- [ ] Should OTP auto-submit be offered as a user setting at all (owner: product).

### 5.1.5 [API clients, keys and OAuth apps](../specs/PKG/PKG-api-clients-and-keys.md)

- [ ] Do we expose OAuth apps (user-delegated access) in phase 2 or later, and who reviews third-party apps for the catalogue? (Product, Security)
- [ ] mTLS for aggregators: do NSE or other MIIs require it? (Integrations)
- [ ] Should the `INT-api-platform-tables` schema gain `owner_membership_id`, `allowed_cidrs`, `resource_restrictions jsonb`, `service_account_id` and `oauth_client.mtls_thumbprints`? Proposed: yes; to be added by the API platform owner. (Engineering)
- [ ] Which secret-scanning programmes can we register our key prefixes with? (Security)

### 5.1.6 [Tenant authentication policies](../specs/PKG/PKG-authentication-policies.md)

- [ ] Which IdP device signals will we accept for `managed` (for example an Entra device compliance claim passed through OIDC, or only client certificates)? (Security)
- [ ] Do we need inbound Shared Signals / CAEP from tenant IdPs in phase 1 for any institution contract? (Security, Product)
- [ ] Sign-in risk scoring: in-house signals only, or a bot/risk provider in each region (data leaves the request path)? (Security, DPO)
- [ ] Should `unit_admin` be allowed to author tighten-only rules, or only request them? (Product)
- [ ] Retention of `auth_policy_decision` (90 days proposed) vs tenant contracts asking for 1 year. (DPO, Security)
- [ ] Do Indian government programme tenants require compliance with specific government security guidelines on admin network restrictions? Assumption: yes for some; legal to confirm per tenant.

### 5.1.7 [External party and counsel identity](../specs/PKG/PKG-external-party-identity.md)

- [ ] Which Indian and Singapore government ID integrations are needed at launch, and is any approval needed for Aadhaar-based verification for our purpose? (Legal, Product)
- [ ] Does any SEBI ODR circular or MII agreement require investor identity verification by the ODR institution, and to which level? (Legal)
- [ ] Is cross-tenant reuse of a verification (with consent) wanted, and under which legal basis in India, Singapore and the US? (DPO, Legal)
- [ ] Are there machine-readable bar registers we can use for `registry_verified` in India, Singapore or US states? (Operations)
- [ ] Retention of the verification outcome after case closure — follow the case retention schedule or shorter? (DPO)
- [ ] Should a party be able to see and revoke counsel they appointed without the case manager? (Product, with tenants)

### 5.1.8 [User provisioning: SCIM, JIT, invitations and deprovisioning](../specs/PKG/PKG-user-provisioning-scim.md)

- [ ] Is SCIM `/Bulk` needed for any launch tenant, or are paged creates enough? (Product)
- [ ] Should group mappings support case-type restrictions (for example "SEBI desk group" can only see SEBI case types) or should that stay in ABAC rules? (Security, with authz group)
- [ ] Do any institutions need SCIM provisioning of panel neutrals from their own directory, given neutrals are often external people? (Product)
- [ ] Outbound SCIM (us pushing to a tenant's HR or IdP) — any demand? Proposed: out of scope. (Product)
- [ ] Legal basis and notice for processing workforce data received by SCIM in India under DPDP: tenant as data fiduciary, Nomology as processor — confirm DPA wording. (Legal)

### 5.2 [Authorization](../specs/PKG/PKG-authorization.md)

- [ ] Do institution tenants need secretariat access to tribunal-only drafts for scrutiny? Now a setting (`access.case.secretariat_sees_tribunal_drafts`), default off; legal and product to confirm per institution's rules.
- [ ] Should a second RLS layer enforce `tribunal_only` in the database? Trade-off: stronger guarantee vs policy complexity and query cost. (Security lead)
- [ ] Record the policy engine decision (TypeScript policies, not a separate policy language) as an ADR; see [[PKG-policy-engine-permission-matrix#questions]]. (Security lead)

### 5.2.1 [RBAC + ABAC (case-level, party-level access)](../specs/PKG/PKG-rbac-abac-case-level-party.md)

- [ ] Confirm the case role list per product (CORD mediation and ODR vs TERES arbitration) with product; `tribunal_secretary` is accepted for TERES arbitration (D6), and its use in CORD is to be confirmed. (Product)
- [ ] Add `case_assignment`, `owning_unit_id` and `case_type_key` to [[DOM-cases-schema]]. (Domain team)
- [ ] Former participants' read access after close: `access.case.read_after_close_days` default 90 (365 for institutions); legal to confirm. (Legal)
- [ ] Do observers (funders, insurers, trainees) need a distinct permission set per type? (Product)

### 5.2.2 [Policy engine, permission matrix per persona](../specs/PKG/PKG-policy-engine-permission-matrix.md)

- [ ] Record the policy engine decision (TypeScript policies vs Cedar or a relationship engine) as an ADR. (Security lead)
- [ ] Rows 4, 13, 26, 40 and 42 depend on institution rules: confirm which are rule-driven via [[PKG-rules-and-decision-engine]] and which are fixed. (Product)
- [ ] Default for parties seeing recordings (row 34): blueprint defaults proposed in [[PKG-settings-access-control#defaults]]. (Product)
- [ ] Is filing on behalf by secretariat (row 11) allowed for all tenants, and what notice goes to the party? Now `access.case.filing_on_behalf_*`. (Legal)

### 5.2.3 [Ethical walls / conflict-based access restrictions](../specs/PKG/PKG-ethical-walls-conflict-based.md)

- [ ] Do institution rules require disclosure of certain walls to parties (for example when a neutral is excluded after a challenge)? Now `access.walls.disclose_to_parties`; legal to confirm defaults per tenant type. (Legal)
- [ ] Should firm-requested walls apply across all tenants in a region (one firm, many institutions)? Proposed: no, per tenant only. (Product, legal)
- [ ] Who is the second approver in small institutions with one secretariat lead? Now `access.walls.designated_officer`. (Product)

### 5.2.4 [Support access and impersonation](../specs/PKG/PKG-support-access-and-impersonation.md)

- [ ] Tenant notification time for break-glass: immediate notification is proposed; contracts with institutions may set a maximum (24 h was the earlier proposal). Legal / account management to confirm.
- [ ] Standing consent for `config_read`: offered in the standard contract or opt-in? Proposed: opt-in by `tenant_owner`. Owner: legal.
- [ ] Session recording (screen) for support sessions on case content: needed, and where stored (in region)? Owner: security.
- [ ] Should a deferred start time be allowed (approve now for a maintenance window tonight)? Proposed: not in v1. Owner: product.
- [ ] Assisted write actions while impersonating ("act as" with the user present) for stuck filings: proposed not in v1; reconsider after 6 months of support data. Owner: security with tenants.

### 5.2.5 [Access explainer and permission simulator](../specs/PKG/PKG-access-explainer.md)

- [ ] Should tenant auditors see the explainer for Nomology support grants (paths via `support_grant`)? Proposed yes, read-only. (Admin group, [[PKG-support-access-and-impersonation]])
- [ ] As-of window: limited to audit retention; confirm minimum 7 years for case-related decisions. (Legal)
- [ ] Self-service explanations for parties: default on for CORD tenants, off for arbitral institutions? (Product)

### 5.2.6 [Authorization data model](../specs/PKG/PKG-authorization-data-model.md)

- [ ] Case manager assignment: [[DOM-cases-schema]] has `assigned_secretary_membership_id` but no `case_assignment` table; propose adding `case_assignment` (multiple staff per case) there. (Domain team)
- [ ] Retention periods for assignments and case roles (7 years assumed). (Legal / DPO)
- [ ] Is a hash partition of `authz_case_role` needed at launch for the SEBI ODR blueprint tenants? Decide after load test. (Platform)

### 5.2.7 [Just-in-time elevation and break-glass access](../specs/PKG/PKG-jit-and-break-glass.md)

- [ ] Should SEBI ODR institution tenants require approval for every tenant_admin activation? Proposed default yes in that blueprint. (Product, compliance)
- [ ] Tenant-owner recovery: what identity evidence does Nomology accept from an institution (board letter, signatory KYC)? (Legal, account management)
- [ ] Break-glass review outcome `not_justified`: does it trigger notification duties to parties whose data was read? Assumption: only if the review finds misuse; legal to confirm per DPDP and tenant contract. (Legal / DPO)
- [ ] SMS alerts for break-glass in India require a DLT-registered template ([[PKG-notification-copy]]). (Integrations)

### 5.2.8 [Service accounts and AI agent principals](../specs/PKG/PKG-non-human-principals.md)

- [ ] Should autonomous agents ever have tenant-wide read scope over case content (for example a docket-wide deadline checker)? Proposed: only through a system purpose, not a tenant agent. (AI group, [[AI-tenant-ai-policy]])
- [ ] Delegation length for long-running agent work beyond 8 hours (for example overnight bundle preparation). (AI group)
- [ ] EU AI Act: if any tenant uses agents in the EU for administration of justice, high-risk obligations may apply. Assumption: not in scope at launch; to be confirmed by legal. (Legal, [[AI-ai-governance-and-impact]])

### 5.2.9 [Permission catalogue](../specs/PKG/PKG-permission-catalogue.md)

- [ ] Should `case:approve` (registration) be split from acceptance of jurisdiction for institutions that treat these as separate secretariat acts? (Product, with [[DOM-cases]])
- [ ] Retention of catalogue releases: proposed 10 years to cover the longest case and limitation period; confirm with legal. (Legal)
- [ ] Should party and counsel permissions for `case.recording:read` be governed by the case-type blueprint instead of a tenant setting? (Product)

### 5.2.10 [System roles, custom roles and permission sets](../specs/PKG/PKG-roles-and-permission-sets.md)

- [ ] Which plans include custom roles? Assumed standard and enterprise. (Commercial, [[BIL-plans-entitlements-and-usage]])
- [ ] Assignment history retention: 7 years after end proposed; legal to confirm against institution record-keeping duties. (Legal)
- [ ] Do court or government programmes need a unit-scoped auditor that sees case content (inspection)? (Product)
- [ ] Under D6 a `user_admin` can assign `secretariat`, which carries case-content permissions the `user_admin` does not hold, because system role contents are fixed. Confirm this reading, or require the assigner to hold the role's permissions for system roles too. (CTO)

### 5.2.11 [Separation of duties and maker-checker](../specs/PKG/PKG-separation-of-duties.md)

- [ ] Default `single_admin_fallback` per blueprint: proposed `delayed_self_approval` for CORD tenants, `owner_approves` for arbitral institutions, `block` for SEBI ODR and court programmes. (Product, compliance)
- [ ] Finance dual-approval threshold default (proposed INR 1,00,000 / SGD 2,000 / USD 1,500 equivalent). (Finance)
- [ ] Should a tribunal's majority decision on an order count as maker-checker for `case.order:publish` in multi-member tribunals? Proposed: out of scope; the tribunal's own process governs. (Legal)

### 5.3 [Storage](../specs/PKG/PKG-storage.md)

- [ ] Is GCS needed at all (no current client requires GCP)? Proposed: keep the interface, ship S3 and Azure Blob only.
- [ ] Recording storage volumes and costs per region (hearings can be many hours of video) — needed for [[INF-cloud-and-iac]] sizing.

### 5.3.1 [Object storage abstraction (S3 / GCS / Azure Blob)](../specs/PKG/PKG-object-storage-abstraction-s3.md)

- [ ] Keep GCS adapter in scope? Proposed: interface only until a client requires it.
- [ ] Which tenants need dedicated buckets by contract? Affects Terraform per tenant.
- [ ] Do we deduplicate identical files across a tenant (content-addressed) to save storage for re-filed exhibits? Proposed: no — simpler deletion and holds.

### 5.3.2 [Encryption, signed URLs and malware scanning](../specs/PKG/PKG-encryption-at-rest-signed-urls.md)

- [ ] Scanner choice per region (self-hosted ClamAV vs cloud-native malware scanning) — cost, detection quality, Azure parity. Owner: security.
- [ ] Should downloads of `attachment` disposition be watermarked with the user's name and time for tribunal-only material?
- [ ] Per-tenant KMS keys for tenants that require crypto-shredding of files on offboarding, vs deleting objects. Proposed: per-region keys plus deletion; per-tenant keys on request.

### 5.4 [Security](../specs/PKG/PKG-security.md)

- [ ] Bot protection approach without puzzle CAPTCHAs (see [[PKG-accessible-authentication-and]]): WAF bot rules only, or an invisible challenge service — which must not send personal data out of region.
- [ ] Do any clients require customer-managed keys (bring-your-own-key) per tenant? Affects [[PKG-encryption-utilities-key]] and [[INF-secrets-and-keys]].

### 5.4.1 [Encryption and secrets client utilities](../specs/PKG/PKG-encryption-utilities-key.md)

- [ ] Bring-your-own-key for institution tenants: required by any client? Owner: sales / legal.
- [ ] Which identity numbers may be stored at all (for example whether full Aadhaar numbers may be held) — legal to confirm; until then store only masked references.
- [ ] Use the AWS Encryption SDK instead of hand-built envelope code? Trade-off: proven format vs Azure parity.

### 5.4.2 [Input sanitisation, CSRF, rate limiting, bot protection](../specs/PKG/PKG-input-sanitisation-csrf-rate.md)

- [ ] Proof-of-work challenge library or edge bot service — which keeps data in region? Owner: security.
- [ ] Do we need a Content Disarm and Reconstruction step for uploaded Office files, beyond malware scanning ([[PKG-encryption-at-rest-signed-urls]])?
- [ ] Rate-limit defaults per plan for the public API — owned by [[APP-api-versioning-rate-limiting]], confirm values.

### 5.5 [Caching](../specs/PKG/PKG-caching.md)

- [ ] Confirm two Redis deployments per region (queues with `noeviction`, cache with LRU) with DevOps — cost impact in [[INF-redis]].
- [ ] Which Next.js cache handler API (legacy `cacheHandler` vs `cacheHandlers` for `'use cache'`) do we target for the Next.js version pinned in [[APP-framework-dependencies]]?
- [ ] Should `personal` classification be allowed in Redis at all, or only in request memo? Proposed: allowed with TTL ≤ 300 s; DPO to confirm.

### 5.6 [Rules and Decision Engine](../specs/PKG/PKG-rules-and-decision-engine.md)

- [ ] Evaluator choice: in-house JSON evaluator vs GoRules Zen vs FEEL / DMN interpreter (carried from [[WF-separation-of-concerns-temporal#questions]]). Owner: platform engineering lead; record as an ADR.
- [ ] Who may publish decision tables in each tenant type? Proposed defaults via permission sets ([[PKG-roles-and-permission-sets]]): institution legal lead approves procedural tables, secretariat lead approves operational ones; Nomology implementation team only for offering-locked tables. Owner: product.
- [ ] Are there decisions where a regulator or institution rule fixes the outcome, so tenants must not edit them (locked tables)? Legal to identify per tenant type; assumption: SEBI ODR timelines are fixed by the applicable circulars and must be locked tables.
- [ ] Create child nodes for the first decision tables (hearing reminder policy, filing fee, response deadline, ODR eligibility).
- [ ] DMN import and export for institutions that already keep rules in DMN tools: needed? Owner: product.

### 5.7 [Settings](../specs/PKG/PKG-settings.md)

- [ ] Confirm with the billing owner the split between entitlements (records) and billing settings ([[PKG-settings-billing-and-plans]]). (owner: CCO)
- [ ] Should unit admins see values of sibling units (read-only) for consistency? Proposed: no. (owner: product)

### 5.7.1 [Tenant terminology and copy overrides](../specs/PKG/PKG-tenant-terminology-and-copy.md)

- [ ] Confirm the initial list of `locked` message IDs with legal. (owner: legal, content design)
- [ ] Are tenant overrides machine-translated as drafts for missing languages (`content.copy.ai_translation_drafts`), or must the tenant supply every language? Proposed: tenant supplies; AI suggestions allowed but marked and reviewed. (owner: i18n lead)
- [ ] Should a SEBI ODR institution be allowed to rename regulator-defined terms, or are those managed by the blueprint? (owner: legal)

### 5.7.2 [User personalisation](../specs/PKG/PKG-personalisation.md)

- [ ] Should tenant admins see aggregate (not individual) preference statistics, for example "40% of counsel chose daily digests"? Proposed: yes, aggregated with a minimum group size of 10. (Product + privacy)
- [ ] Remappable shortcuts in Phase 5, or only "turn off single-key shortcuts" (which satisfies WCAG 2.2 SC 2.1.4 [R1]) at first? Proposed: turn-off first, remap later. (Accessibility lead)
- [ ] Do we allow export and import of a user's views between tenants they belong to? Proposed: no; definitions may reference tenant-specific custom fields. (Product)
- [ ] Confirm the `(account)` route group with the admin group's route map. (Admin group)

### 5.7.3 [Settings catalogue (all levels)](../specs/PKG/PKG-settings-catalogue.md)

- [ ] Should a dedicated tenant role for privacy (for example `privacy_officer`) own `data.*` instead of `security_admin`? Many institutions name a grievance or data protection officer. (owner: authz group, DPO)
- [ ] Should tenants see the settings of features they are not entitled to (with an "upgrade" badge) or should those be hidden? Proposed: shown, read-only, for discoverability; hidden for court programmes. (owner: product)

### 5.7.3.1 [Access control settings](../specs/PKG/PKG-settings-access-control.md)

- [ ] Finance dual-approval threshold default per currency. (Finance)
- [ ] Should `access.case.secretariat_sees_tribunal_drafts` be allowed only where the institution's rules provide for award scrutiny? (Legal, product)
- [ ] Court programme `read_after_close_days` of 3650 is an assumption pending each programme's record rules. (Legal)
- [ ] Is `access.review.auto_remove_on_no_response` safe for neutrals on long-running cases? Proposed: never auto-remove case roles, only tenant roles. (Product)

### 5.7.3.2 [AI settings](../specs/PKG/PKG-settings-ai.md)

- [ ] Budget unit shown to tenants: currency, credits or tokens (carried from [[AI-cost-controls]]). (owner: billing)
- [ ] Should `ai.retention.prompt_output_bodies = metadata_only` be offered, given it weakens our ability to explain past outputs? (owner: legal, AI governance lead)
- [ ] Defaults for court and government programmes to be validated with the first such tenant. (owner: product)

### 5.7.3.3 [Billing, plans and entitlement settings](../specs/PKG/PKG-settings-billing-and-plans.md)

- [ ] Confirm SEBI ODR fee rules (who pays, amounts, timing) for the SEBI ODR blueprint defaults. (owner: legal)
- [ ] Billing period boundary: is the tenant's local month needed for Indian institutions? (owner: CCO, finance)
- [ ] Should tenants be able to self-upgrade plans or buy add-ons in the console? Proposed: not at launch. (owner: CCO)
- [ ] Invoice prefix changes only at financial-year start: confirm for India, Singapore and US entities. (owner: tax adviser)

### 5.7.3.4 [Branding, content and locale settings](../specs/PKG/PKG-settings-branding-content.md)

- [ ] Should SEBI ODR institutions be prevented from renaming regulator-defined terms (managed terminology), or only warned? (owner: legal)
- [ ] May unit themes use different logos (a court programme inside a larger tenant) or only a different display label? Proposed: different theme versions owned by the tenant. (owner: product)
- [ ] Is `limit.locales` a commercial limit at all, or should all platform-supported languages be available on every plan? (owner: CCO)
- [ ] Protected-name list for impersonation control: who maintains it and how often? Proposed: platform security, reviewed quarterly. (owner: security lead)

### 5.7.3.5 [Case and workflow settings](../specs/PKG/PKG-settings-cases-and-workflows.md)

- [ ] Should unit admins be able to change `case.reference.format` for their unit, or only the prefix? (Product)
- [ ] KYC-before-submit for SEBI ODR claimants is an assumption; confirm with legal against current SEBI ODR circulars and the MII process. (Legal)
- [ ] Is `case.procedure.default_confidentiality = sealed` allowed at case scope without a tribunal order? (Legal)
- [ ] Region default schedules (working hours) need confirmation from regional operations. (Regional ops)

### 5.7.3.6 [Data retention and privacy settings](../specs/PKG/PKG-settings-data-and-privacy.md)

- [ ] Legal / DPO to confirm every proposed period and every regional bound in this catalogue per tenant type and region. (owner: DPO)
- [ ] Assumption: the DPDP Third Schedule erasure timelines and 48-hour pre-erasure notice apply only to the listed classes of data fiduciaries (large e-commerce, gaming and social media platforms) and not to our tenants; to be confirmed. (owner: legal)
- [ ] Who is the data fiduciary for party data in each tenant type (the institution, with Nomology as processor), and therefore who must be named in `data.notice.fiduciary_contact`? (owner: legal)
- [ ] Do SEBI circulars or MII agreements require minimum retention of ODR records? (owner: legal)
- [ ] Should a dedicated `privacy_officer` tenant role own this catalogue instead of `security_admin`? (owner: authz group, DPO)

### 5.7.3.7 [Integration settings](../specs/PKG/PKG-settings-integrations.md)

- [ ] Webhook retry window: platform maximum 168 hours, or longer for court programmes? Stripe-style platforms retry for up to 3 days [R1]. (Product)
- [ ] App install requests by non-admins (for example counsel requesting a practice-management app): keep admins only, as in workspace app-approval models where members request and owners approve [R2]? (Product)
- [ ] Should calendar sync ever go beyond free / busy (for example writing hearing events), given `.ics` attachments [R3] already cover invites? (Product)

### 5.7.3.8 [Notification settings](../specs/PKG/PKG-settings-notifications.md)

- [ ] Should a court programme be able to set `notify.channel.email.track_opens = true` for evidence? Default off; legal to advise per jurisdiction. (Legal)
- [ ] Confirm quiet-hours bounds (4–12 hours) against TRAI rules for transactional SMS in India; assumption: no time restriction for service and transactional messages, to be confirmed by legal. (Legal)

### 5.7.3.9 [Personal preference settings](../specs/PKG/PKG-settings-personal.md)

- [ ] Should language and time zone follow the person across tenants in a region by default (proposed: per membership with the "apply in region" option)? (Product)
- [ ] Is `personal.privacy.usage_analytics = essential_only` enough to satisfy consent requirements for product analytics in each region, or is analytics opt-in needed in some? (Privacy owner)
- [ ] Should a dyslexia-friendly font option be offered? Depends on font licensing and the multi-script font stacks in [[PKG-typography-and-multi-script]]. (Accessibility lead)

### 5.7.3.10 [Platform operations settings](../specs/PKG/PKG-settings-platform-operations.md)

- [ ] Default `access.support.consent_mode` for the CORD tenant: is `standing_config_read` acceptable given Nomology operates CORD? (legal)
- [ ] `platform.support.session_recording`: required for `case_read` and break-glass sessions? (security)
- [ ] Should `access.support.*` and `access.bulk.*` move to [[PKG-settings-access-control]] for one place to find all `access.*` keys? Proposed: stay here, referenced there. (authz group)
- [ ] Maintenance windows per region: confirm with tenants that hold hearings on Sunday mornings in the US region. (regional ops)
- [ ] Export window and deletion defaults per tenant type (proposed values above) against standard contracts. (account management, legal)

### 5.7.3.11 [Security and identity settings](../specs/PKG/PKG-settings-security-and-identity.md)

- [ ] Is WhatsApp OTP acceptable as a first factor for parties in India, and under which provider terms? (Security, Legal)
- [ ] Confirm whether any SEBI ODR circular or MII agreement requires investor identity verification beyond email or mobile control. (Legal)
- [ ] Confirm the platform blocked-countries list and its legal basis per entity. (Legal, Compliance)
- [ ] Should `unit_admin` be allowed to shorten session timeouts, or should only tenant scope exist? Current proposal: yes, tighten only. (Security)
- [ ] Plan names now follow [[BIL-plans-entitlements-and-usage]] (`starter`, `standard`, `enterprise`; decision D11). Open: which settings groups need their own entitlement key rather than a plan tier. (Billing)
- [ ] Is Singpass login (as opposed to Myinfo for verification) needed for any Singapore tenant at launch? (Product)

### 5.7.4 [Settings and configuration data model](../specs/PKG/PKG-settings-data-model.md)

- [ ] Confirm the 8-year evidence period for superseded configuration with legal, and the rule that values referenced by pins of retained cases are kept. (owner: DPO)
- [ ] Should user preference writes also go through change sets for tenants that require it (court programmes)? Proposed: no; they are personal choices. (owner: product)
- [ ] The multi-tenancy team to accept the proposed `tenant` columns (`primary_offering`, `offerings`, `parent_tenant_id`, `customer_account_id`, `sandbox` type). (owner: multi-tenancy lead)
- [ ] Is a hash-partitioned `case_config_pin` needed at launch for the largest SEBI ODR tenant? Assumption: not before 20 M rows. (owner: platform engineering)

### 5.8 [Configuration and Customisation](../specs/PKG/PKG-configuration-and-customisation.md)

- [ ] Do institution tenants want Nomology's implementation team to author changes in their production tenant with a tenant admin as checker, or always configure themselves? Carried to [[PKG-configuration-lifecycle#questions]]. (owner: CEO, COO)
- [ ] Should tenant-defined entity types (beyond custom fields on core entities) become an artefact kind in a later phase? See [[PKG-metadata-management-entity#questions]]. (owner: product)

### 5.8.1 [Metadata management (entity definitions, custom fields)](../specs/PKG/PKG-metadata-management-entity.md)

- [ ] Are tenant-defined entity types (for example "Settlement offer") needed in phase 4, or can they wait? Proposed: wait.
- [ ] Should `sensitive_personal` custom fields be field-encrypted automatically via [[PKG-encryption-utilities-key]]? Proposed: yes, which makes them non-searchable.
- [ ] Do aggregator report formats (NSE, MSME) require fixed custom field keys across tenants? Proposed: yes, shipped as managed fields in the SEBI ODR blueprint. (owner: product, reporting)
- [ ] Should unit-specific fields be allowed (an office that collects extra data)? Proposed: no; use case-type selection instead. (owner: product)

### 5.8.2 [Forms and form builder](../specs/PKG/PKG-forms-and-form-builder.md)

- [ ] Should forms support e-signature of the submission ([[INT-e-signature]]) or is consequential confirmation with step-up enough for filings?
- [ ] Is a reading-level indicator required for SEBI ODR investor-facing forms? Owner: product with legal.
- [ ] Offline or low-bandwidth mode for the runner?
- [ ] Should the admin copilot generate a first draft of a form from an uploaded paper form (PDF)? Proposed: yes, as a draft for review, subject to [[AI-tenant-ai-policy]]. Owner: AI group.

### 5.8.3 [Workflow templates](../specs/PKG/PKG-workflow-templates.md)

- [ ] Which processes start as code workflows vs blueprints. Proposed: case lifecycle as blueprints (from library blueprints), notice service, eBundling and pipelines as code workflows exposed as registered subprocesses.
- [ ] Expression grammar: in-house (proposed, small, shared as `@nomology/expr` by gateways, automation conditions and decision outputs) vs an existing safe language (for example CEL or JSONata).

### 5.8.4 [Document and notification templates](../specs/PKG/PKG-document-and-notification.md)

- [ ] PDF engine: headless Chromium vs alternatives; accessibility tagging quality decides. Owner: platform engineering with accessibility lead.
- [ ] Do tribunals need DOCX output for orders and awards to edit offline? Proposed: yes for drafts, PDF for issued versions.
- [ ] Which documents have formats prescribed by regulators or institutions (for example SEBI ODR notices)? Legal to list; such templates are locked.
- [ ] Who may edit translations of locked templates: tenant translators, or only certified translators recorded per language? (Legal + content)

### 5.8.5 [Branding and theming](../specs/PKG/PKG-branding-and-theming.md)

- [ ] May a tenant use a custom domain for sign-in, and if so which trust cues show the platform behind it (owner: security lead, with [[MT-tenant-resolution]] and [[PKG-domain-verification]]).
- [ ] Do white-label tenants want the platform name hidden entirely from the footer? Decided for now: no; `compact` attribution is the most a plan can offer (owner: CEO / CCO to confirm).
- [ ] Should platform support be able to edit a tenant's theme on request, or only revert (owner: product).
- [ ] Unit themes: are different logos per unit needed (court programmes inside a larger tenant), or only different display labels? (owner: product)

### 5.8.5.1 [Tenant theme schema and validation](../specs/PKG/PKG-tenant-theme-schema-and.md)

- [ ] Is 60 seconds acceptable for activation to take effect, or do tenants expect instant preview-to-live (owner: product).
- [ ] Confirm the allowed logo aspect ratio range with real tenant logos from launch institutions (owner: design).
- [ ] Do we need a separate theme for the CORD consumer-facing public filing entry, or does the CORD tenant theme cover it (owner: CORD product lead).

### 5.8.6 [Thresholds and alert configuration (consumed by Observability)](../specs/PKG/PKG-thresholds-and-alert.md)

- [ ] Which tenant-facing thresholds need tenant-type bounds (for example SEBI ODR turnaround) so that regulated timelines cannot be loosened? Legal and product to decide.
- [ ] Do tenants want alerts delivered to external tools (email distribution lists, Teams, Slack) via webhooks ([[APP-webhooks-outbound]]) or connections ([[INT-connections-admin]])?
- [ ] Evaluator implementation: inside our BullMQ workers versus the observability vendor's alerting with per-tenant rules.
- [ ] Confirm with the workflow group that all case-level timers live in SLA policies ([[WF-sla-and-business-calendars]]). (owner: workflow group)

### 5.8.7 [Configuration change lifecycle](../specs/PKG/PKG-configuration-lifecycle.md)

- [ ] Should a masked copy of production configuration plus anonymised case data ever be offered in sandboxes (useful for testing reports)? Proposed: no at launch; DPO to decide. (owner: DPO)
- [ ] Is 14 days the right default approval expiry? (owner: product)
- [ ] Should SEBI ODR and court tenants have `access.change_control.review_all_changes = true` by default in their blueprints? Proposed: yes for court programmes, no for SEBI ODR. (owner: product, legal)
- [ ] May a Nomology implementation engineer act as author and a tenant admin as checker in the tenant's production tenant, with a recorded approval, so that institutions do not have to build their own configuration? Carried over from [[PKG-configuration-and-customisation]]. (owner: CEO, COO)
- [ ] Emergency rollback post-hoc review window: 2 business days proposed. (owner: security lead)

### 5.8.8 [Configuration packages and tenant blueprints](../specs/PKG/PKG-configuration-packages.md)

- [ ] Is tenant configuration (fee schedules, institution templates) "customer data" under our contracts, so that moving a promotion package across regions needs contractual cover? Proposed: treat as customer confidential and require tenant-owner approval. (owner: legal)
- [ ] Should tenants be able to share packages with each other (a template marketplace)? Proposed: not at launch; only Nomology-curated extensions. (owner: product)
- [ ] Confirm the SEBI ODR timelines and fee rules to encode as managed constraints in `blueprint.sebi_odr_institution`. (owner: legal)
- [ ] Court programme blueprint content depends on the first court customer. (owner: CEO)
- [ ] Should snapshot packages be signed with a tenant-specific key so a tenant can prove an export is theirs? Proposed: platform key plus a tenant reference hash is enough. (owner: security lead)

### 5.8.9 [Configuration scope hierarchy and inheritance](../specs/PKG/PKG-configuration-scope-hierarchy.md)

- [ ] Is one primary offering per tenant enough, or do some tenants need the unit to choose the offering (for example a CORD programme run inside a TERES institution)? (owner: product)
- [ ] Confirm which keys need tenant-type targeting at launch; proposed list: retention minimums, SEBI ODR timeline bounds, investor charter display, DPDP notice requirements. (owner: legal)
- [ ] Should a unit admin be able to lock values for their sub-units, or only tenant admins? Proposed: unit admins may lock within their own subtree. (owner: product, authz group)
- [ ] Should `explain` be available to `auditor` for case-scope values on cases they cannot otherwise open? Proposed: no; explanation follows case access. (owner: security lead)
- [ ] Assumption: units nest at most 5 deep ([[MT-tenancy-and-identity-schema]]); resolution cost grows with depth, so deeper trees need a new design. (owner: platform engineering)

### 5.9 [Feature flags](../specs/PKG/PKG-feature-flags.md)

- [ ] In-house provider versus a self-hosted open-source flag service per region? Proposed: in-house until experiments are needed.
- [ ] Should flag changes in production for regulated tenants (SEBI ODR, court programmes) require notifying the tenant in advance? Proposed: release notes cover it; pilot cohorts are agreed with the tenant. (owner: product)

### 5.10 [Audit trail](../specs/PKG/PKG-audit-trail.md)

- [ ] Confirm retention per tenant type (arbitral institution, SEBI ODR institution, CORD) and whether institution rules require audit records to follow the case file. Owner: legal.
- [ ] Do tenants want the anchor digest published to them (for example a monthly signed digest email) so they can verify independently? Owner: product.
- [ ] Should failed sign-in attempts for unknown users be stored in tenant audit or only in security telemetry? Proposed: security telemetry only (no tenant user exists).
- [ ] Is 60-second sealing acceptable to security, given unsealed events are protected only by grants and triggers until sealed?

### 5.10.1 [Audit log schema](../specs/PKG/PKG-audit-log-schema.md)

- [ ] Confirm the 13-month hot window with support and compliance (how far back do tenants search interactively?). Owner: product.
- [ ] Retention per tenant type and whether institutions need audit records kept as part of the case file. Owner: legal.
- [ ] Is a per-tenant hashing key for `changes` acceptable, given key destruction on offboarding makes old hashes unverifiable against values (the chain still verifies)? Owner: security.
- [ ] `xid8` horizon sealing relies on transaction IDs surviving failover; confirm behaviour on RDS / Aurora and Azure Flexible Server failover. Owner: DevOps.

### 5.11 [Notifications](../specs/PKG/PKG-notifications.md)

- [ ] Is email open tracking acceptable as supporting evidence of service for any tenant, given privacy concerns? Default off (`notify.evidence.email_open_counts_as_evidence`); legal to advise per jurisdiction.
- [ ] Which channels are valid for legal service per tenant type (email, SMS, WhatsApp)? Encoded per tenant in service rules; legal to confirm.
- [ ] Shared platform WhatsApp number per region vs per-tenant numbers (setting `notify.sender.whatsapp.number_mode`; default shared).
- [ ] Do we need a print-and-post channel for service on parties without electronic contact?
- [ ] Should a notification centre in each persona shell show mandatory-notice explanations inline? Proposed: yes ([[PKG-personalisation]]).

### 5.11.2 [Notification copy](../specs/PKG/PKG-notification-copy.md)

- [ ] Which entity registers DLT headers and templates in India: NTPL for all tenants, or each tenant as principal entity (owner: legal, COO).
- [ ] Confirm the DLT template categories and variable limits with the chosen SMS provider (owner: integrations lead).
- [ ] Which languages are needed at launch for SEBI ODR investor notifications (owner: product).
- [ ] May email subjects include the case title for counsel and neutrals if a tenant asks (proposed: no, reference only) (owner: security lead, legal).

### 5.11.3 [Notification policy administration](../specs/PKG/PKG-notification-policies.md)

- [ ] Which event types besides `legal_service` and `auth` may a tenant mark "bypass quiet hours"? Proposed: only events flagged `urgent_eligible` in the event catalogue (hearing changes within 24 hours, hearing room link changes on the hearing day). (Legal + product)
- [ ] Should policy changes apply to running cases immediately (proposed, except event types pinned at case start) or only to new cases? (Legal)
- [ ] Is an in-app read receipt acceptable as acknowledgement for any rule set's service requirements? (Legal, per rule set)
- [ ] US recipients: confirm whether TCPA consent rules apply to our non-marketing case SMS; assumption: informational messages to numbers provided by the recipient need prior express consent, to be confirmed by legal. (Legal)
- [ ] Split sender identity into its own node: done, see [[PKG-notification-sender-identity]]. Decide whether unit-specific senders are needed in Phase 5. (Product)

### 5.11.4 [Notification sender identity and domain authentication](../specs/PKG/PKG-notification-sender-identity.md)

- [ ] Who is the DLT principal entity for each India tenant type: the tenant, or NTPL on its behalf? Legal to confirm; affects who registers headers and templates. (Legal)
- [ ] Confirm Singapore sender ID registration requirements and the US registration path with the chosen providers. (CTO office)
- [ ] Should the platform receive DMARC aggregate reports for tenant domains (needs a reporting mailbox and parser), or only check DNS? Proposed: DNS checks only in Phase 3. (Platform engineering)
- [ ] BIMI (brand logos in inboxes) for institutions that ask for it: later phase? (Product)

### 5.12 [Search](../specs/PKG/PKG-search.md)

- [ ] Confirm Postgres full-text first; define the measurable trigger for OpenSearch (for example p95 > 500 ms at the largest tenant, or need for Indic analysers).
- [ ] Should tribunal-only material be searchable at all? Proposed: yes, for tribunal principals only, in a separate index table.
- [ ] Multilingual analysis for Hindi, Kannada, Chinese and others: which analysers, and is trigram good enough at launch?

### 5.13 [Data access](../specs/PKG/PKG-data-access.md)

- [ ] Should `withTenant` also set `app.case_ids` or similar for a second RLS layer on `tribunal_only` rows, or is case-level filtering application-only? (See [[PKG-rbac-abac-case-level-party]].)
- [ ] Is RDS Proxy ever acceptable instead of PgBouncer? [[INF-pgbouncer]] says it must be validated first; until then PgBouncer is mandatory.
- [ ] Outbox table per domain schema or one shared `platform.outbox_event`? Proposed: one shared table partitioned by day.
- [ ] Do we allow `Serializable` transactions in request paths, or only in workers?
- [ ] Owner for reference data per region (see [[PKG-reference-and-seed-data#questions]]).

### 5.13.1 [Reference and seed data catalogue](../specs/PKG/PKG-reference-and-seed-data.md)

- [ ] Which ISO 3166 / ISO 4217 source do we license or mirror, and who checks it quarterly? Owner: platform engineering.
- [ ] Who in each region owns holiday calendar updates, and what is the service level for an ad-hoc holiday declaration? Owner: operations.
- [ ] Do aggregator formats (NSE for SEBI ODR matters, MSME) need their own code lists (for example category codes) as reference data? Owner: product, with [[RPT-aggregators]].
- [ ] Case type list per product (CORD, TERES, HKIAC CMP) to be confirmed. Owner: product.
- [ ] Assumption: `is_sanctioned_jurisdiction` is maintained from the screening provider, not by hand. To be confirmed with compliance.

### 5.13.2 [Retention and deletion schedule by table](../specs/PKG/PKG-retention-and-deletion-schedule.md)

- [ ] Legal / DPO to confirm every period in the schedule per tenant type and jurisdiction; all are assumptions now. Owner: DPO.
- [ ] Finance to confirm tax record retention for NTPL, TAPL and the US entity. Owner: finance.
- [ ] Compliance to confirm KYC / AML record-keeping periods. Owner: compliance.
- [ ] Do institutions require awards to be kept permanently? If yes, `keep` end action for awards per tenant.
- [ ] Should anonymised case skeletons be kept for statistics (GAR, ODR insights reports, [[RPT-industry-marketing]]) or deleted? Owner: product and DPO.
- [ ] Purpose-specific database roles (`retention_job` here, `audit_sealer` in [[PKG-audit-log-schema]], `auth_resolver` and `outbox_relay` in [[INT-api-platform-tables]]) are not in the canonical role set (`nomo_owner`, `nomo_migrator`, `nomo_app`, `nomo_worker`, `nomo_reporting`, `nomo_platform_ops`). Either add them to the role inventory in [[MT-app-connects-as-a-non]] as NOLOGIN or narrow roles, or run deletion under `nomo_platform_ops` as [[MT-isolation-strategy]] states. (owner: CTO with platform lead)

### 5.14 [UI / design system](../specs/PKG/PKG-ui-design-system.md)

- [ ] Confirm React Aria Components as the headless behaviour layer and record it as an ADR (owner: frontend lead).
- [ ] Visual regression: self-hosted Playwright snapshots (proposed) or a hosted service such as Chromatic; decide on cost and whether story data may leave our CI (owner: design system lead).
- [ ] Who is the named design owner for the system, and is there a budget for a part-time accessibility specialist reviewing component changes? (owner: CTO)
- [ ] Do we publish Storybook to tenant implementation staff (read-only, behind SSO) or keep it internal only? (owner: product)

### 5.14.1 [Design tokens and foundations](../specs/PKG/PKG-design-tokens-and-foundations.md)

- [ ] Confirm Style Dictionary as the build tool and the minimum version that supports the DTCG 2025.10 resolver module, or whether we write a small resolver step ourselves (owner: design system lead).
- [ ] Figma: who may edit variables in the Figma library, and do we accept the one-way repo → Figma sync (owner: product design).
- [ ] Is compact density wanted in the neutral workspace for award drafting, or only in queues (owner: product).
- [ ] Do we need a native mobile token output in the next 12 months (owner: CTO).

### 5.14.1.1 [Colour and contrast](../specs/PKG/PKG-colour-and-contrast.md)

- [ ] Should high-contrast mode target 7:1 for all text (proposed) or only body text (owner: accessibility lead).
- [ ] Approve the automatic dark-mode variant for tenant brand colours, or require tenants to supply a dark brand colour explicitly (owner: product).
- [ ] Confirm the seven status tones with the domain team before the case state machine is final (owner: domain lead, cases).

### 5.14.1.2 [Typography and multi-script fonts](../specs/PKG/PKG-typography-and-multi-script.md)

- [ ] Confirm the font choices (Inter, Source Serif 4, JetBrains Mono, Noto families) with product design, and check each licence for embedding in PDFs (owner: design lead; legal for licence confirmation).
- [ ] Which Indian languages do launch tenants issue documents in? This decides which serif Indic families are bundled into the PDF renderer (owner: product).
- [ ] Is Arabic or Hebrew needed by any Singapore or US tenant in the next 12 months (owner: CCO).

### 5.14.1.3 [Colour modes and user preferences](../specs/PKG/PKG-colour-modes-and-user.md)

- [ ] Should forced-colours users get a hint about the platform's own high-contrast mode, or is that redundant? (Accessibility lead)

### 5.14.1.4 [Data visualisation palette](../specs/PKG/PKG-data-visualisation-palette.md)

- [ ] Product design review of the proposed categorical values for appearance and brand fit (owner: product design).
- [ ] Choose the chart library and confirm it supports patterns, markers and keyboard focus on data points (owner: reporting lead).
- [ ] Should the CVD distance threshold be 12 (proposed) or higher (owner: accessibility lead).

### 5.14.1.5 [Print and formal document theme](../specs/PKG/PKG-print-and-formal-document-theme.md)

- [ ] Confirm with launch institutions whether they need their own award layouts and who approves them (owner: CCO).
- [ ] Confirm the default paper size per region and whether any institution mandates one (owner: product).
- [ ] Should eBundle page stamps be placed in the footer (proposed) or in the top inline-end corner as some practice directions prefer (owner: TERES product lead).

### 5.14.2 [Button and icon button](../specs/PKG/PKG-button-and-icon-button.md)

- [ ] Do we allow disabled buttons at all in party journeys, or always keep them enabled and show validation (proposed: avoid disabled) (owner: product design).

### 5.14.3 [Form fields](../specs/PKG/PKG-form-fields.md)

- [ ] Do we mark required or optional fields by default across the platform (proposed: mark required, since most legal forms are mostly required) (owner: content design).

### 5.14.4 [Combobox and people picker](../specs/PKG/PKG-combobox-and-people-picker.md)

- [ ] Should neutrals with declared conflicts be hidden or shown as disabled with the reason (proposed: shown disabled for secretariat, hidden for parties) (owner: domain lead, neutrals; legal).
- [ ] Minimum query length of 2 characters for CJK names may be too high; confirm 1 for CJK locales (owner: i18n lead).

### 5.14.5 [Date and time picker with time zones](../specs/PKG/PKG-date-and-time-picker-with.md)

- [ ] For date-only deadlines, confirm whose time zone defines end of day: the seat of arbitration, the institution, or the filing party (owner: legal, with [[PKG-calendars-and-deadline]]).
- [ ] Confirm `@internationalized/date` as the date library (ties to the React Aria ADR) (owner: frontend lead).

### 5.14.6 [File upload dropzone](../specs/PKG/PKG-file-upload-dropzone.md)

- [ ] Maximum per-file size per tenant plan (proposed default 200 MB; audio for transcription larger) (owner: product, with [[BIL-plans-entitlements-and-usage]]).

### 5.14.7 [Data table](../specs/PKG/PKG-data-table.md)

- [ ] Do secretariat users need saved views (named filter sets) in the first release (owner: product, secretariat console).
- [ ] Is grid mode needed beyond the transcriber queue (owner: frontend lead).

### 5.14.8 [Modal dialog and consequential confirmation](../specs/PKG/PKG-modal-dialog-and-consequential.md)

- [ ] Which actions require `typed` or `step-up` level? Proposed: issue award and withdraw claim typed; change bank details and payouts step-up (owner: product, security lead).

### 5.14.9 [Alerts, toasts and status messages](../specs/PKG/PKG-alerts-toasts-and-status.md)

- [ ] Agree the keyboard shortcut for reaching toasts and check it does not clash with screen reader shortcuts (owner: accessibility lead).

### 5.14.10 [Stepper and multi-step form](../specs/PKG/PKG-stepper-and-multi-step-form.md)

- [ ] Draft retention period and whether drafts are visible to the tenant secretariat before filing (proposed: not visible) (owner: legal, with [[PKG-retention-and-deletion-schedule]]).
- [ ] Can counsel share a draft with co-counsel before filing (owner: product).

### 5.14.11 [Case timeline](../specs/PKG/PKG-case-timeline.md)

- [ ] Which event types are visible to each persona and confidentiality tier; needs the domain matrix from [[DOM-cases]] (owner: domain lead, cases).

### 5.14.12 [Status and deadline badges](../specs/PKG/PKG-status-and-deadline-badges.md)

- [ ] Should deadline thresholds be tenant-configurable (proposed: yes, within 1–14 days and 12–72 hours) (owner: product).

### 5.14.13 [Tenant and role switcher](../specs/PKG/PKG-tenant-and-role-switcher.md)

- [ ] Is persona switching within a tenant also a full navigation (proposed yes, since route groups differ) (owner: frontend lead).
- [ ] Do we show memberships in other regions in the list (requires a global directory lookup) (owner: architecture, with [[MT-data-residency-2]]).
- [ ] Should unit admins with several unassociated units be able to choose "All my units" as one scope? Proposed: yes, as a union scope, if [[PKG-authorization-data-model]] supports multi-unit assignments in one decision. (owner: authz group)

### 5.14.14 [Document viewer controls](../specs/PKG/PKG-document-viewer-controls.md)

- [ ] Bundle reference format per institution (owner: TERES product lead).
- [ ] Should print be allowed for parties by default (owner: product, legal).

### 5.14.15 [Design system component accessibility contract](../specs/PKG/PKG-design-system-component.md)

- [ ] Do we waive axe `moderate` findings or fail on them too (proposed: waiver needed) (owner: accessibility lead).
- [ ] Budget and schedule for testing components with disabled users (proposed: twice a year with recruited participants, paid) (owner: product).
- [ ] Confirm the device mix for parties from analytics once CORD traffic exists (owner: product analytics).

### 5.15 [Data retention, legal hold and deletion](../specs/PKG/PKG-data-retention-legal-hold-and.md)

- [ ] Legal to confirm periods per record type and tenant type (arbitral institution, SEBI ODR institution, CORD), including whether institutions keep awards permanently.
- [ ] Logs cannot be erased per record; confirm that time-based log retention with no case content in logs is acceptable to the DPO.
- [ ] Backups: confirm the statement for privacy notices that deleted data persists in encrypted backups until they expire (for example 35 days).

### 5.16 [Calendars and deadline computation](../specs/PKG/PKG-calendars-and-deadline.md)

- [ ] Legal to confirm counting conventions per tenant type (for example whether the day of service is excluded, what happens when the last day is a holiday, deemed service rules for email). Until confirmed, conventions are explicit parameters per rule set.
- [ ] Who publishes public holiday calendars per jurisdiction and how quickly after official notification? Owner: operations (see [[PKG-reference-and-seed-data#questions]]).
- [ ] Should a calendar correction create a human task for each affected open deadline, or a single digest for the secretariat?
- [ ] Multi-participant deadlines across time zones: is the seat's time zone always authoritative? Assumption: yes, unless the rule set says otherwise.

## 6 Domain Modules

### 6.1 [Cases](../specs/DOM/DOM-cases.md)

- [ ] Confirm the generic status set with legal / operations for each tenant type, in particular whether `in_scrutiny` and `proceedings_closed` exist in SEBI ODR practice.
- [ ] SEBI ODR stage timelines and claim-value thresholds: obtain the current consolidated values from legal and record them in decision tables (assumption until then).
- [ ] Should orders and awards become their own context (drafting, approval, correction, interpretation), or remain filings with special rules here?
- [ ] Do representatives keep access to documents filed during their representation after it ends (CASE-BR-18)? Default no; confirm per tenant type.
- [ ] Multi-party and consolidated cases: model consolidation as a link between cases or as a merge? Needed for arbitral institutions.
- [ ] Emergency arbitration: separate case or a sub-proceeding of the main case?
- [ ] Do aggregator-originated cases need the MII reference to be unique per tenant, and is it shown to parties?

### 6.1.1 [Service of notices and proof of delivery](../specs/DOM/DOM-service-of-notices-and-proof.md)

- [ ] For each rule set, which events count as service: provider delivery receipt, portal acknowledgement, or a deemed time after dispatch? Legal to confirm (assumption: configurable per rule set; default requires delivery receipt or acknowledgement).
- [ ] Is WhatsApp acceptable as a service channel for SEBI ODR and CORD tenants, or only as a reminder channel? Legal to confirm.
- [ ] Do we need a qualified timestamp (for example a trusted timestamping authority) on proof-of-service certificates, or is the database clock with hash chaining in the audit log sufficient?
- [ ] Postal / courier integration: manual entry only, or integrate with a courier API in India first?

### 6.1.2 [Cases schema](../specs/DOM/DOM-cases-schema.md)

- [ ] Should case-participant visibility be enforced in RLS as well as in the authorisation layer for sealed cases? Owner: security lead.
- [ ] Do custom fields ever hold sensitive personal data (for example disability accommodations)? If so, encrypted custom fields are needed. Owner: product.
- [ ] Cross-package migration ordering (cases depends on neutrals and documents tables): one migration stream per region or per package? Owner: platform engineering.
- [ ] Assumption: volume figures are placeholders until sales forecasts for SEBI ODR and HKIAC CMP are available.
- [ ] Should `case_rule_set_pins` become a view over `config.case_config_pin` once every rule set ships inside a blueprint? Owner: DOM cases team with configuration lead.
- [ ] Group assignees: should a `case_assignment` to a group give every current group member the case role, or only make the case visible in the group's queue until a member takes it? Proposed: queue only. Owner: authz lead.

### 6.2 [Neutrals](../specs/DOM/DOM-neutrals.md)

- [ ] Legal to confirm the disclosure form versions per rule set (s.12 forms for Indian seats; institution forms elsewhere) and who signs (e-signature via [[INT-e-signature]] or click-to-sign).
- [ ] SEBI ODR allocation: confirm whether rotation is required and the capacity limits per conciliator / arbitrator (assumption until confirmed).
- [ ] Should repeat-appointment counting (NEU-BR-9) also consider related entities (group companies), and who maintains entity relationships?
- [ ] Do neutrals want one cross-tenant profile they control? If yes, design a consent-driven copy, not a shared row.
- [ ] Is sanctions screening of neutrals required (for example when paying fees across borders)? Finance / legal to confirm.

### 6.2.1 [Neutrals schema](../specs/DOM/DOM-neutrals-schema.md)

- [ ] Is `pg_trgm` approved as an installed extension on managed Postgres in every region (AWS and Azure)? Owner: infrastructure.
- [ ] Name matching across scripts (Devanagari, Tamil, Chinese) needs a transliteration library; choose one and decide whether it runs in the database or the app.
- [ ] Should calendar-synced busy blocks be stored at all, or queried live from the calendar provider at scheduling time?

### 6.3 [Transcribers](../specs/DOM/DOM-transcribers.md)

- [ ] Can transcribers located outside the tenant's region work on that tenant's recordings (remote access from another country)? This is a cross-border access question under DPDP / PDPA; legal to confirm per region.
- [ ] Is certification a legal statement in any jurisdiction we serve (for example a certified transcript for court use), and does it need e-signature?
- [ ] Should turnaround penalties reduce vendor bills as well as client invoices? Commercial decision.
- [ ] Accuracy measurement: word accuracy on a sampled minute, or a weighted error score by category? Proposed: weighted score; confirm with the transcription manager.

### 6.3.1 [Transcribers schema](../specs/DOM/DOM-transcribers-schema.md)

- [ ] Store working text in Postgres (simpler search and diffing) or object storage (current proposal, keeps large text out of the database)?
- [ ] Is a trigger acceptable under our migration standards, or should TRN-BR-4 be an application check with an advisory lock?

### 6.4 [Hearings](../specs/DOM/DOM-hearings.md)

- [ ] Video provider per region: which providers can host meetings and store recordings in India, Singapore and the US, and do we need our own media servers anywhere? Owner: integrations lead with [[INT-video-conferencing-for-hearings]].
- [ ] Is a recording ever a legal requirement for SEBI ODR hearings? Legal to confirm.
- [ ] Physical venues: does any tenant need us to integrate with an external venue booking system?
- [ ] Should cross-tenant neutral double-booking be detectable with the neutral's consent (shared free / busy across their profiles)?

### 6.4.1 [Hearings schema](../specs/DOM/DOM-hearings-schema.md)

- [ ] Keep `session_bookings` in sync by repository code (current proposal) or by trigger from `hearing_sessions`? A trigger guarantees sync for every writer.
- [ ] Do in-person hearings need room-level resources (interpretation booths, screens) with their own no-overlap constraints?

### 6.4.2 [Hearing room accessibility](../specs/DOM/DOM-hearing-room-accessibility.md)

- [ ] Which video providers in each region offer an SDK that lets us replace all controls and pin tiles? Drives the exception list. Owner: integrations.
- [ ] CART provider(s) per region and how their feed is embedded (iframe vs caption stream API).
- [ ] Legal: confirm whether RPwD s.46 duties and the SEBI 2025 circular reach ODR institutions and private arbitral institutions directly, or only through contract.
- [ ] Should live captions be retained as an interim aid until the certified transcript is delivered? Needs tribunal and privacy view.

### 6.5 [Documents](../specs/DOM/DOM-documents.md)

- [ ] Should duplicate uploads (same SHA-256 already in the case) be linked automatically or warned about? Proposed: warn and allow.
- [ ] Is a trusted timestamp needed for filing times in some jurisdictions, beyond the database clock and audit chain?
- [ ] SEBI ODR: confirm whether the ODR institution must review documents before they reach the respondent.
- [ ] Email files (MSG, EML) with attachments: expand attachments as separate documents linked as `annex_of`?

### 6.5.1 [eBundling](../specs/DOM/DOM-ebundling.md)

- [ ] PDF engine: reuse the existing TERES eBundling design (Stirling-PDF based) as a service on `documents-render`, or a library-based worker (for example qpdf plus a PDF library)? Decision needed before Phase 4; candidate for an ADR.
- [ ] Default re-issue strategy per tenant type: `insert_suffix` (preserves citations) is proposed for arbitral institutions.
- [ ] Should parties be able to build their own sections in the platform, with the secretariat combining them?
- [ ] Page and size limits per plan ([[BIL-plans-entitlements-and-usage]]).

### 6.5.2 [Documents schema](../specs/DOM/DOM-documents-schema.md)

- [ ] Add a composite FK guaranteeing `current_version_id` belongs to the same document (needs `UNIQUE (tenant_id, id, document_id)` on versions)?
- [ ] Should all document views (not only restricted ones) be recorded? Volume vs evidential value; product and legal.

### 6.5.3 [Accessible documents and eBundles](../specs/DOM/DOM-accessible-documents-and.md)

- [ ] Choose and verify the tagged-PDF renderer and validator in CI (licence and accuracy for Indic and CJK scripts).
- [ ] Should the accessible-copy request automatically pause or extend related deadlines, or always need a tribunal decision? Legal / product.
- [ ] Do tenants need DOCX or HTML versions of awards as accessible alternatives in addition to PDF?

### 6.6 [Invoices and vendor bills](../specs/DOM/DOM-invoices-and-vendor-bills.md)

- [ ] Finance / legal per region: invoice numbering and e-invoicing obligations for tenants (they are the sellers), and whether the platform must generate e-invoice payloads for Indian tenants above the threshold.
- [ ] Does the platform ever hold client money (deposits) itself, or only record what the tenant's bank account holds? Proposed: record only; money flows to the tenant's own gateway or bank account. Legal to confirm there is no payment-aggregator licensing implication.
- [ ] FEMA: Indian tenants receiving fees from foreign parties; is any reporting data needed from the platform? Finance.
- [ ] Should neutrals submit bills in the platform or should bills be generated from fee terms and time entries automatically?

### 6.6.1 [Invoices and vendor bills schema](../specs/DOM/DOM-invoices-and-vendor-bills-schema.md)

- [ ] Confirm invoice numbering period and format rules per region (finance).
- [ ] Should the ledger become a full double-entry ledger (debit / credit pairs) to simplify reconciliation with Odoo, or stay single-entry by account?
- [ ] Are trigger-based append-only rules acceptable under our migration standards (see also [[DOM-transcribers-schema#questions]])?

## 7 Tasks and Workflows

### 7.1 [Workflow engine](../specs/WF/WF-workflow-engine.md)

- [ ] Is a Temporal Schedule or a BullMQ repeatable job the default for low-stakes periodic sweeps (search re-index, thumbnail backfill)? Proposed: BullMQ for sweeps with no legal effect, Temporal Schedules for anything reported to a regulator or aggregator.
- [ ] Outbox relay: run as a BullMQ repeatable job per region or as a dedicated relay process? Owner: platform engineering.
- [ ] Do we allow signal-with-start from the outbox relay for every process, or only for case-level workflows?
- [ ] Should automation rules be allowed to start a library subprocess (for example "collect deposit") on a case, or only signal steps the blueprint declares? Proposed: signals only. Owner: product.

### 7.2 [Background jobs and queues](../specs/WF/WF-background-jobs-and-queues.md)

- [ ] Buy BullMQ Pro for group-based per-tenant fairness and rate limiting, or keep our Redis semaphore? Owner: platform engineering.
- [ ] Separate Redis instances for queues and cache per region (recommended to avoid eviction of queue keys), or one cluster with `noeviction`? Owner: DevOps with [[INF-redis]].
- [ ] Who may replay dead letters in production, and does replay of a tenant's job need tenant approval?

### 7.3 [Human tasks](../specs/WF/WF-human-tasks.md)

- [ ] Should the inbox also show "waiting on others" tasks (for example the secretary sees that the respondent's response is due)? Proposed: yes, read-only, derived from case deadlines rather than tasks.
- [ ] Do parties (unrepresented) get tasks, or only deadlines and notifications? Proposed: controlled by `workflow.task.party_tasks_enabled` (on for CORD and SEBI ODR blueprints), with plain-language guidance from [[DOC-plain-language-guidance-for]]. Owner: product.
- [ ] Skills taxonomy: free tags per tenant or a platform list (languages, panels, specialisations)? Proposed: platform prefixes (`lang:`, `panel:`, `region:`) with tenant-defined values. Owner: product.
- [ ] Should capacity consider task weight (a scrutiny task counts more than an acknowledgement)? Owner: product.

### 7.4 [Long-running pipelines (transcription, OCR, bundling, AI processing)](../specs/WF/WF-long-running-pipelines.md)

- [ ] Which ASR and diarisation models are available in-region for each language we need (English, Hindi, other Indian languages, Mandarin, Cantonese)? Determines `NoInRegionModel` exposure. Owner: AI lead.
- [ ] Separate `documents-render` worker pool (proposed) — confirm sizing and whether it also serves eBundling heavy stages.
- [ ] Per-tenant concurrency caps for pipelines (proposed: 20 document pipelines and 4 transcription pipelines per tenant at once), configurable for large tenants?

### 7.5 [Separation of Concerns (Temporal)](../specs/WF/WF-separation-of-concerns-temporal.md)

- [ ] Rules engine choice: in-house JSON evaluator vs GoRules Zen vs a FEEL / DMN interpreter
- [ ] Visibility store: Postgres vs OpenSearch per region
- [ ] Which processes start as code workflows vs interpreter workflows. Proposed: case lifecycle runs as blueprints from Phase 3 using library blueprints; notice service, eBundling and pipelines stay code workflows called as registered subprocesses
- [ ] Note: the summary of [[PKG-rules-and-decision-engine]] points to "7.6" for this design; the layer model lives here in 7.5. Correct the cross-reference.
- [ ] [[ADR-workflow-engine]] (approved, not edited) lists as a revisit trigger that the interpreter may prove too limited. Record the interpreter versioning strategy (Auto-Upgrade plus patching, pure core) as its own ADR. Owner: CTO.

### 7.6 [Entity state machines](../specs/WF/WF-entity-state-machines.md)

- [ ] Defence in depth: add a database trigger that rejects status changes unless the transaction set `app.sm_transition = 'on'` (set by `transition()` with `set_config(..., true)`)? Protects against writes from migrations, scripts or a missed code path. Proposed: yes for cases, documents and invoices.
- [ ] Use XState v5 for definitions (gains visual tooling) or keep the small in-house definition (current proposal: in-house, with `toMermaid()`)?
- [ ] Should `allowedCommands()` evaluate guards that need database reads for every list row, or only on detail views? Proposed: detail views only.
- [ ] Which case commands are `blueprintInvocable`? Proposed: `start_scrutiny`, `register` (when the rule set allows automatic registration), `start_conciliation`, `refer_to_arbitration`, `begin_constitution`, `close_case`; never `issue_award`, `terminate` or `withdraw`, which need a human actor. Owner: product with legal.

### 7.7 [AI steps and agents in workflows](../specs/WF/WF-ai-steps-and-agents.md)

- [ ] Workflow group: confirm the `ai_step` node binds to AI step definitions as sketched, add the `legal_effect` tag on decision tables, and confirm `accepted_by_policy` facts are allowed downstream. The process-definition model now states the D8 exception. (owner: workflow group)
- [ ] Platform floor for auto-accept threshold (proposed 0.85) and minimum calibration examples (proposed 30 per label). (owner: AI platform lead)
- [ ] Is `accepted_by_policy` acceptable to institutions at all, or do some (for example court programmes) require `always` for every AI step? Decided for the review pass (D8): tenant setting `ai.workflow_steps.allow_auto_accept`, off by default in every blueprint; final confirmation is a CTO decision. (owner: CTO, product with tenants)
- [ ] Should corrected auto-accepted facts re-run downstream routing automatically or create a task for the case manager? (owner: workflow group)

### 7.8 [Automation rules (trigger, condition, action)](../specs/WF/WF-automation-rules.md)

- [ ] Should tenants be able to trigger rules from inbound integration events (for example a payment gateway callback or an MII status update) directly, or only from our normalised domain events? Proposed: domain events only. Owner: integrations group ([[INT-integration-framework]]).
- [ ] Is `set_field` on custom fields enough, or do tenants need to set core case fields (priority, assigned secretary)? Proposed: `assign_secretary` as a separate action with its own permission. Owner: product.
- [ ] Maker-checker for automation publishing: default on for all tenant types, or off for CORD tenants with fewer staff? Owner: product with [[PKG-separation-of-duties]].
- [ ] BullMQ per-tenant fairness relies on the open question in [[WF]] (BullMQ Pro groups or our own token bucket) [R2]. Owner: platform engineering.

### 7.9 [Process definition model (case-type blueprints)](../specs/WF/WF-process-definition-model.md)

- [ ] Should `cases` carry `case_type_key` and `blueprint_version_id` directly (denormalised from `wf.case_process`) for simpler reporting joins? Owner: DOM cases team with [[DOM-cases-schema]].
- [ ] Retention of superseded blueprint versions: aligned with configuration versions in [[PKG-settings-data-model#retention]] (8 years after superseded), and never earlier than the record retention of the last case pinned to the version. Confirm with legal and [[PKG-retention-and-deletion-schedule]]. Owner: legal.
- [ ] Is a blueprint allowed to span offerings (one blueprint used by both CORD and TERES tenants)? Proposed: no; one offering per blueprint. Owner: product.
- [ ] Unit-specific variants: one blueprint with unit-scoped settings overrides (proposed) or separate case types per unit? Owner: product.
- [ ] Assumption: the SEBI ODR stages, timelines and status codes must be taken from the current SEBI circulars and NSE format; to be confirmed by legal before the starter blueprint is published. Owner: legal.
- [ ] Should library fragments be versioned independently and pinned (proposed) or inlined into the blueprint at publish? Owner: platform engineering.

### 7.10 [SLAs, timers and business calendars](../specs/WF/WF-sla-and-business-calendars.md)

- [ ] Assumption: SEBI ODR timelines (for example conciliation and arbitration completion periods) are counted as calendar days and are fixed by the circular, so they are procedural deadlines in a locked decision table, not tenant SLAs. To be confirmed by legal. (Legal)
- [ ] Should partial-day closures (for example a half-day before a festival) be supported in business schedules? Proposed: yes, as closure intervals. (Product)
- [ ] Do parties see SLA targets (for example "the secretariat aims to review your filing within 2 business days")? Proposed: optional per policy with plain-language copy. (Product, content)
- [ ] Platform SLAs owed by Nomology to tenants (uptime, support response) are out of scope here and belong to [[RPT-platform-performance]]; confirm that no tenant contract expects them in the same report. (Commercial)

### 7.11 [Workflow authoring studio](../specs/WF/WF-workflow-authoring-studio.md)

- [ ] Canvas library: `@xyflow/react` (React Flow) with our own keyboard layer, or a list-first editor with a read-only diagram rendered by Mermaid? Decision depends on an accessibility spike. Owner: frontend lead.
- [ ] Real-time co-editing (multiple designers in one draft) vs soft lock (proposed for launch). Owner: product.
- [ ] Should approvers be able to comment on individual elements in review (threaded comments stored with the version)? Proposed: yes, Phase 5. Owner: product.
- [ ] Which ATAG Part B success criteria do we commit to for content produced in the studio (forms and notices)? Owner: accessibility lead with [[APP-accessibility-wcag-2-1-aa]].
- [ ] Does the platform console reuse this route tree with a different data source, or a separate tree under `/platform/blueprints`? Owner: admin group ([[APP-platform-admin-and-support]]).

### 7.12 [Workflow simulation and test runs](../specs/WF/WF-workflow-simulation.md)

- [ ] Coverage minimums per tenant type: is 100% of procedural gateways achievable for large institutional blueprints, or should the minimum be configurable down to 90% with a reviewer acknowledgement? (Product with legal)
- [ ] Should simulation traces be shareable outside the tenant (for example with Nomology implementation staff) without support access? Proposed: only through approved support access ([[PKG-support-access-and-impersonation]]). (Security)
- [ ] Load forecasting (tasks per queue per week from history replay) needs staff capacity data; is that in scope for Phase 5? (Product)
- [ ] Do court or government programme tenants require independent sign-off of test evidence before go-live? (Legal)

### 7.13 [Workflow versioning, publishing and in-flight migration](../specs/WF/WF-workflow-versioning.md)

- [ ] Minimum support window for an old interpreter major contract: proposed 24 months, or tied to the longest case duration per tenant type. Owner: CTO (see [[ADR-workflow-interpreter-versioning]]).
- [ ] Should `content_follows_latest` be allowed for document templates that produce legal documents (procedural orders, awards)? Proposed: no, only for notification templates and non-legal documents. Owner: legal.
- [ ] Do parties need to consent to, or be able to object to, a migration that changes their obligations, or is notice enough? Assumption: notice is enough where the institution's rules allow; to be confirmed by legal per tenant type. Owner: legal.
- [ ] Two-approver rule for procedural changes: default on for SEBI ODR and court tenants, off for CORD tenants? Owner: product.
- [ ] ADR follow-up: [[ADR-workflow-engine]] is approved and is not edited here. Its revisit trigger "interpreter plus rules engine proves too limited" should be checked after the first three tenants' blueprints are live; this note adds the interpreter contract and Auto-Upgrade choice, which may merit a separate ADR ("Interpreter versioning strategy"). Owner: CTO.

## 8 Native AI

### 8.1 [AI gateway](../specs/AI/AI-ai-gateway.md)

- [ ] Gateway form: regional service (proposed) or in-process library; record as an ADR.
- [ ] Does the agent runtime run inside the gateway service or as a sibling service `ai-agents` (proposed sibling, so the gateway keeps no tool execution)? Record as an ADR.
- [ ] Providers and models per region (India, Singapore, US, and Azure deployments); confirm in-region processing, zero-retention and no-training terms for each.
- [ ] Is a self-hosted open-weight model needed for any region, and who operates GPU capacity?
- [ ] Out-of-region exceptions: allow per tenant with written agreement (now modelled) or forbid entirely?
- [ ] Timeouts and latency budgets per capability (proposed values above).
- [ ] Do we stream tokens to the browser for drafting assistance, and if so how are output guardrails applied to a stream (buffer by sentence or check at end before the draft can be saved)?

### 8.2 [Prompt management](../specs/AI/AI-prompt-management.md)

- [ ] Which slots do tenants actually need at launch (terminology, rules reference, tone)? Proposal: terminology and rules reference only.
- [ ] Should a tenant's acceptance testing be able to pin an older prompt version, and for how long at most (proposed 30 days)?
- [ ] Do institutions want to review and approve prompts used for their neutrals' drafting assistance before rollout?
- [ ] Language of prompts for non-English output (for example Hindi summaries): one prompt per language or a language variable?
- [ ] When a base prompt release makes a tenant agent fail its evaluation, how long does the tenant keep the old base version (proposed 14 days, aligned with [[AI-agent-configuration#models]])?

### 8.3 [RAG](../specs/AI/AI-rag.md)

- [ ] Vector store: pgvector in the regional Postgres (proposed, keeps RLS and backups uniform) or a separate store; record as an ADR. Check filtered ANN search performance with tenant and case filters at expected volume.
- [ ] Embedding model per region and its dimension; multilingual support for Hindi and other Indic-language documents.
- [ ] Field-level encryption for `rag_chunks.text`, or rely on database encryption at rest?
- [ ] Should tribunal-only documents be indexed at all, or only on request by the tribunal?
- [ ] Retention: do chunks follow the document's retention exactly, or are they deleted earlier when the case closes?

### 8.4 [Guardrails](../specs/AI/AI-guardrails.md)

- [ ] Which in-region detector for names and addresses (open-source NER self-hosted, or provider service) per region?
- [ ] Party-name pseudonymisation default per tenant type (now a setting, `ai.data.pseudonymise_party_names`; blueprint defaults in [[PKG-settings-ai#defaults]]): confirm with institutions.
- [ ] Retention of blocked outputs (proposed 30 days, setting `ai.retention.blocked_outputs_days`).
- [ ] Neutrality rules wording: agree with tenants and legal what counts as "advice" or "prediction" ([[APP-voice-tone-and-content-style]]).
- [ ] Should tenant tool policies support conditions on tool arguments (for example block `message.draft` to certain recipient types), or only on roles and units at launch?

### 8.5 [Human-in-the-loop](../specs/AI/AI-human-in-the-loop.md)

- [ ] Do institutions require disclosure to parties when AI assisted a procedural order or award, and in what form? Tenant decision, captured as `ai.disclosure.neutral_use` in [[PKG-settings-ai]].
- [ ] Is a "must open full output" control acceptable to neutrals, or too intrusive? (Setting `ai.review.require_open_before_approve`, locked on for T3.)
- [ ] Expiry period for unreviewed outputs (default 30 days, now a setting).
- [ ] CTO decision (D8): confirm the `accepted_by_policy` state, the only path where a person does not approve each item. The review pass aligned [[WF-process-definition-model]], [[WF-ai-steps-and-agents]] and [[PKG-settings-ai]] to it: off by default, calibrated internal `classify` and `extract` steps only, no effect on the merits or on parties' rights. (owner: CTO, legal)
- [ ] Do tenants want access to rubber-stamp metrics for their own users, given they may be used for performance management? (Default off.)

### 8.5.1 [AI-generated text labelling and review](../specs/AI/AI-ai-generated-text-labelling-and.md)

- [ ] Which institutions require an AI-assistance statement in orders or awards, and with what wording? (Tenant decisions; do not assume.)
- [ ] Should approved AI-assisted text carry a visible label inside the issued document, or only in the audit record?
- [ ] Should messages drafted with AI help be labelled to recipients?
- [ ] Hindi and other language versions of the captions disclaimer: who approves the translation?

### 8.6 [Cost controls](../specs/AI/AI-cost-controls.md)

- [ ] Budget unit shown to tenants: tokens, credits or currency?
- [ ] Do budgets reset on the calendar month or the billing period?
- [ ] Which features are allowed to exceed the single-request 5 percent cap (bundle summaries)?
- [ ] Should a unit be allowed to borrow unused budget from the tenant pool automatically? Proposed: no, to keep allocations meaningful.
- [ ] Retention period of the usage ledger per billing entity (NTPL, TAPL, US entity); confirm with finance.

### 8.7 [AI governance and impact assessment](../specs/AI/AI-ai-governance-and-impact.md)

- [ ] Name the control owner, reviewer and backup.
- [ ] Is Nomology pursuing ISO/IEC 42001 certification, and for which entities (NTPL, TAPL, US entity) and by when?
- [ ] Legal view on EU AI Act applicability, given EU parties may appear in cases administered by our tenants, including current application dates for Annex III obligations.
- [ ] Do any institutions or regulators (for example via SEBI-recognised MIIs) have their own rules on AI use in ODR that tenants must follow? Do not assume; collect from tenants at onboarding into `ai.disclosure.*` settings.
- [ ] Are umbrella assessments for tenant agents and AI steps acceptable to auditors, or does each T2 agent need its own short assessment?
- [ ] Evidence retention periods (proposed 6 years) to be confirmed.

### 8.8 [Tenant-configured assistants and agents](../specs/AI/AI-agent-configuration.md)

- [ ] Do tenants want party-facing procedural help agents (answering only from published rules and FAQs, never about a specific case)? Needs a policy decision on unreviewed AI output to parties and an impact assessment. (owner: CTO, legal)
- [ ] Minimum number of tenant test cases before publish (proposed 10). (owner: AI platform lead)
- [ ] Should tenants be able to connect external knowledge (SharePoint, document management) through connectors in phase 2? (owner: integrations group)
- [ ] Default conversation retention (proposed 30 days) and whether neutrals' conversations need a shorter default. (owner: legal)
- [ ] Should Nomology review every T2 agent before publish, or only monitor? Proposed: monitor, with right to suspend. (owner: AI governance lead)

### 8.9 [AI audit and transparency records](../specs/AI/AI-ai-audit-and-transparency.md)

- [ ] Should parties and counsel be able to request the AI record of their own case (beyond the disclosure page), and through whom? (owner: legal, product)
- [ ] Minimum retention of AI metadata when `ai.retention.prompt_output_bodies = metadata_only`. (owner: legal)
- [ ] Does the export format need to match any regulator or MII template? Assumption: no; collect from tenants. (owner: compliance)

### 8.10 [Tenant AI policy and feature controls](../specs/AI/AI-tenant-ai-policy.md)

- [ ] Legal: is offering a party AI opt-out advisable, and does any law in our regions give parties a right to object to AI processing of their submissions? (owner: Nomology legal)
- [ ] Legal: EU AI Act classification of `drafting_assist` and `bundle_summary` for tenants with EU parties; whether Article 6(3) applies to assistive, human-approved features [R2]. (owner: legal)
- [ ] Which institutions require disclosure of neutrals' AI use, and in what form? Collect per tenant at onboarding; do not assume. (owner: product with tenants)
- [ ] Grace period after a material AI notice change (proposed 30 days). (owner: legal)
- [ ] Should unit admins be allowed to hold `ai.budget:update` for their unit only? Proposed yes. (owner: product)
- [ ] Sampling rate for logged allows (proposed 1 percent plus all T3). (owner: security)

## 9 Integrations and Plugins

### 9.1 [Integration framework](../specs/INT/INT-integration-framework.md)

- [ ] Is a generic integration-hub product (open source) worth using for OAuth token management, or is the in-house vault enough (proposed: in-house)?
- [ ] Inbox raw-body retention for non-evidential events (proposed 90 days).
- [ ] Which categories allow `tenant_byo` at launch: payments and calendar (as before), plus messaging and e-sign for institutions (proposed in [[PKG-settings-integrations#defaults]])?
- [ ] Egress control: per-connector host allow-lists at the network layer ([[INF-networking]]) in addition to code checks?
- [ ] Should payload data kind tags come from Prisma model field annotations (generated) or from explicit tags at each call site? Proposed: generated from a field classification registry shared with [[SEC-data-classification]].

### 9.1.1 [Integration connections administration](../specs/INT/INT-connections-admin.md)

- [ ] Should `tenant_byo` be allowed for messaging (email and SMS) from Phase 3, given legal-notice evidence depends on provider receipts we do not contract for? Proposed: yes for email and SMS, with a mandatory receipt-capability check in the probe. (Product + legal)
- [ ] Do we expose provider-side deletion evidence to tenants in the offboarding pack, or keep it internal? (Privacy owner)
- [ ] Who may approve a `tenant_byo` connection whose provider processes data outside the tenant region: `security_admin` only, or also Nomology `platform_security` for regulated blueprints (SEBI ODR)? (Security)
- [ ] Unit-level BYO accounts (a unit's own e-sign contract): needed in Phase 5 or later? (Product, TERES)
- [ ] Per-user connections beyond calendar (for example a neutral's own e-sign identity)? (Product)

### 9.1.2 [Connector data policies](../specs/INT/INT-connector-data-policies.md)

- [ ] Should tenants be allowed to define their own data kinds (for example "settlement amount"), or only map custom fields to platform kinds? Proposed: map only. (Product + security)
- [ ] Should the policy also govern **inbound** data (for example refusing KYC results that include images)? (Security)
- [ ] Monitor-only mode for tenants rolling out a stricter policy: allowed in sandbox only (proposed) or also in production for 7 days? (Security)
- [ ] Which data kinds may a transcription vendor receive for SEBI ODR matters? Assumption: none, as SEBI ODR conciliation is largely online without recorded hearings; to be confirmed by legal. (Legal)
- [ ] Align AI provider governance in [[AI-tenant-ai-policy]] to the same layers and evaluator, or keep a separate engine? Proposed: same evaluator, separate rule sets. (AI group)

### 9.2 [Common integrations](../specs/INT/INT-common-integrations.md)

- [ ] Choose providers per category and region (table above); record each as an ADR.
- [ ] Video: managed provider with in-region recording versus self-hosted media servers per region (see [[INT-video-conferencing-for-hearings]]).
- [ ] Odoo hosting and topology: one database with a company per entity, or separate databases per entity and region?
- [ ] Is two-way calendar sync wanted for neutrals in Phase 7, or is `.ics` plus free / busy enough?
- [ ] Secondary email provider per region for failover: needed for SEBI ODR notice volumes? If yes, configure as `integration.default_connection.messaging.secondary`.
- [ ] Confirm which categories are "core" (proposed: email and SMS only).

### 9.2.1 [Video conferencing for hearings](../specs/INT/INT-video-conferencing-for-hearings.md)

- [ ] Option A (managed provider) or B (self-hosted) per region; record as an ADR after a residency and cost comparison.
- [ ] Are breakout rooms ever recorded? Proposed: never, and the UI states this.
- [ ] Recording format: composite only, or separate audio tracks per speaker to improve transcription?
- [ ] Is a phone dial-in fallback required by any institution's rules?
- [ ] Retention of provider-side copies: delete immediately after verified copy (proposed).

### 9.2.2 [E-signature](../specs/INT/INT-e-signature.md)

- [ ] Legal: for each tenant type and document (awards under the seat's arbitration law, settlement agreements, declarations), which signature methods are acceptable?
- [ ] Select the ESP and the global provider; confirm regional storage for Singapore and US.
- [ ] Support signers' own digital signature certificates (Class 3 DSC) for neutrals in a later phase?
- [ ] What attributes does the ESP's signer certificate expose, and which do we store?
- [ ] Accessibility of the ESP and provider signing pages (see [[INT-third-party-component]]).

### 9.2.3 [KYC and sanctions screening provider](../specs/INT/INT-kyc-and-sanctions-screening.md)

- [ ] Legal / compliance: for each entity and tenant type, is Nomology or the tenant the obligated party for KYC and screening, and under which law?
- [ ] Which lists are mandatory per entity (table above is a proposal)?
- [ ] Are parties (not only payees) screened, and only when the tenant enables it?
- [ ] Retention of KYC and screening records per entity (to align with [[RPT-aml-kyc-sanctions-screening]]).
- [ ] Accessible alternatives to document and liveness checks for parties with disabilities.

### 9.2.4 [Messaging providers](../specs/INT/INT-messaging-providers.md)

- [ ] Confirm India DLT requirements and who registers as principal entity (Nomology or each tenant) for SMS.
- [ ] Is WhatsApp acceptable as a service channel under any institution's rules, or only as a reminder?
- [ ] Select SMS and WhatsApp providers per region.
- [ ] Do we need a secondary email provider per region for failover?

### 9.2.5 [Accounting sync](../specs/INT/INT-accounting-sync.md)

- [ ] Odoo topology (multi-company versus separate databases) and hosting location.
- [ ] Should Odoo or the platform own numbering for these journals? Proposed: platform numbers, Odoo stores them.
- [ ] Deferred revenue schedules in Odoo: available in the edition we use, or handled by journal entries we generate?
- [ ] Bank statement import and matching: in Odoo (proposed).

### 9.2.6 [Third-party component accessibility](../specs/INT/INT-third-party-component.md)

- [ ] Legal: confirm our duty to provide accessibility evidence for embedded vendors to regulated tenants.
- [ ] Will any help / chat widget or bot-protection script be used at all? Proposed: none in Phase 5.
- [ ] Accessibility as a scored criterion in each vendor selection (video, e-sign, KYC, gateway): agree weighting with procurement.
- [ ] Who owns the register (accessibility lead or vendor management)?

### 9.3 [Plugin model](../specs/INT/INT-plugin-model.md)

- [ ] Is there a real need for third-party code running inside the platform (for example a tenant's custom validation)? If yes, choose a sandbox (separate container per tenant, or WebAssembly with no network) and record an ADR.
- [ ] Who may publish tenant-private plugins: tenant admins, or only Nomology's implementation team (current default)?
- [ ] Should there be a public marketplace listing of external apps, and what review would a listed app need (security questionnaire, pen-test summary, privacy notice)?
- [ ] Should counsel (non-staff) be able to request apps for their own use, for example a practice-management sync? Proposed: no in Phase 5.

### 9.4 [Public API and webhooks](../specs/INT/INT-public-api-and-webhooks.md)

- [ ] Domain and hostnames for the API per region and for Azure-hosted tenants.
- [ ] Do we also offer personal access tokens for counsel (user-bound, for practice-management tools), or only service principals in Phase 5 (proposed)? Decision belongs with [[PKG-api-clients-and-keys]].
- [ ] Should API clients be able to act on behalf of a named user (token exchange) for audit attribution?
- [ ] SDKs: generate TypeScript and Python clients from OpenAPI in Phase 5, or later?
- [ ] Minimum deprecation notice: 12 months proposed; check against institutional contracts.
- [ ] Should tenants see a per-client "explain this denial" view (scope versus object permission), reusing [[PKG-access-explainer]]? Proposed: yes in Phase 6.

### 9.4.1 [Outbound webhooks](../specs/INT/APP-webhooks-outbound.md)

- [ ] Retry window: 72 hours default with a 168-hour maximum for court programmes (proposed in [[PKG-settings-integrations]]); confirm with institutions that have weekend maintenance windows.
- [ ] Do any tenants need mTLS for deliveries? Egress IP ranges per region are published (decided).
- [ ] Should payload "fat" mode (including changed fields with personal data) ever be offered? Decided: never in v1 (setting locked to `thin`).
- [ ] Should paused endpoints have a maximum pause (for example 7 days) after which they become disabled? (Product)

### 9.4.1.1 [Webhook event catalogue](../specs/INT/INT-webhook-event-catalogue.md)

- [ ] Are institution or aggregator receivers asking for any personal data in events (for example party names for routing)? If so, offer it only behind a separate scope.
- [ ] Should invoice and payment events for case fees ([[DOM-invoices-and-vendor-bills]]) be added in Phase 5?
- [ ] Event retention for `/v1/events`: 30 days proposed.

### 9.4.2 [Public API — Cases and parties](../specs/INT/INT-public-api-cases-and-parties.md)

- [ ] Which case types and actions are exposed to external clients per tenant (configurable allow-list proposed)?
- [ ] Do counsel-firm integrations exist in Phase 5, or only institution integrations?
- [ ] Should party contact searches be allowed at all through the API (privacy review)?

### 9.4.3 [Public API — Documents and filings](../specs/INT/INT-public-api-documents-and-filings.md)

- [ ] Is `received_at` the legal filing time, or the time the upload completed (matters for deadlines at midnight)? Proposed: `received_at` of the filing call, after all items are available; legal to confirm per rule set.
- [ ] Maximum file size for parties versus institutions; recordings via API at all?
- [ ] Should clients be able to request bundle generation through the API in a later version?

### 9.4.4 [Public API — Hearings and scheduling](../specs/INT/INT-public-api-hearings-and.md)

- [ ] Do institutions want the API to **fix** a hearing time (secretariat integration), not only propose? Proposed: later version.
- [ ] Should participant availability (busy / free) be accepted from counsel calendars through the API?
- [ ] Is exposing `venue.address` for in-person hearings acceptable to all tenants?

### 9.4.5 [Tenant admin API](../specs/INT/INT-tenant-admin-api.md)

- [ ] Should SSO configuration ever be manageable through the API? Proposed: console only in v1 (lock-out risk). (owner: identity group, [[PKG-sso-saml-oidc-per-tenant]])
- [ ] Is creating API clients through the API ever needed (for example for an institution's automation platform)? Proposed: no. (owner: security)
- [ ] Should human-held OAuth tokens be allowed to decide approvals through the API, or only the console? (owner: security, with [[PKG-separation-of-duties]])

### 9.4.6 [Aggregator intake API](../specs/INT/INT-aggregator-intake-api.md)

- [ ] Does NSE (and each future aggregator) call a platform API, or require us to integrate with its own interface? This decides whether this node or a connector is built.
- [ ] Obtain the current NSE field list and stage names for SEBI ODR status reporting; do not infer them.
- [ ] Which party contact data does intake carry, and under what notice to the party (DPDP)?
- [ ] Status feed retention: 400 days proposed.
- [ ] Is aggregator access to a tenant approved by the tenant admin (proposed) or set by contract with Nomology?

### 9.4.7 [API platform tables](../specs/INT/INT-api-platform-tables.md)

- [ ] Security review of the `auth_resolver` policy and the `outbox_claim_batch` SECURITY DEFINER function.
- [ ] Keep the FK from `webhook_delivery` to the partitioned outbox, or rely on transactional ordering?
- [ ] Should the outbox record every domain event (also used by billing, search indexing) or only webhook-relevant ones? Proposed: one shared outbox for all consumers.
- [ ] Retention of revoked API client records (proposed: tenant life + 1 year).
- [ ] Is a maximum of 2 mTLS thumbprints per client enough for aggregators that rotate certificates on their own schedule? (owner: integrations, with [[PKG-api-clients-and-keys]])

## 10 Billing and Subscription

### 10.1 [Plans, entitlements and usage metering](../specs/BIL/BIL-plans-entitlements-and-usage.md)

- [ ] Commercial team to set real plans, prices and limits per currency; the tables are placeholders.
- [ ] Billing period boundary: UTC month for all tenants or the tenant's local month? Now a setting with default `utc_month` (`billing.period.boundary`, [[PKG-settings-billing-and-plans]]); the commercial decision sets the default per tenant type.
- [ ] Is "active case" the right billable unit for SEBI ODR tenants with high volumes of small claims, or should it be "cases registered in period"?
- [ ] Should neutrals empanelled with the tenant ever count as seats (for example if the tenant pays for their access)?
- [ ] Build or buy the rating engine (in-house versus Lago / Stripe Billing); this node assumes in-house on Postgres.
- [ ] AI hard ceiling behaviour: now a tenant setting (`billing.usage.ai_ceiling_behaviour`, default `block_ai_features`); confirm the default per tenant type.
- [ ] Is `limit.locales` a commercial limit at all? (owner: CCO)

### 10.2 [Invoicing, tax and multi-currency](../specs/BIL/BIL-invoicing-taxes-gst-singapore.md)

- [ ] Tax adviser (name) to confirm the treatment table, rates, SAC code, invoice wording and rounding rule for each entity.
- [ ] Is NTPL above the e-invoicing turnover threshold now, and which reporting window applies? Use a GSP or the direct IRP API?
- [ ] Is TAPL GST-registered, or likely to cross the registration threshold, and which customers will it invoice?
- [ ] US entity: which states have economic nexus, and which sales tax service (for example a hosted tax API) to use?
- [ ] FX rate source per entity for functional-currency amounts.
- [ ] Invoice timing: combined monthly invoice in arrears plus advance base fee (proposed) or separate invoices?
- [ ] Do any institutional contracts require invoices in the client's own format or portal upload (vendor portals)?
- [ ] Retention periods per entity (proposed 8 / 8 / 7 years).

### 10.3 [Payment gateway integration, dunning, refunds](../specs/BIL/BIL-payment-gateway-integration.md)

- [ ] Choose the INR gateway (RBI-authorised payment aggregator) and the SGD / USD gateway; is one provider acceptable for all three?
- [ ] Legal: confirm that case fees settling directly into the tenant's own merchant account keeps Nomology outside payment aggregator rules in India, and the equivalent position in Singapore and the US.
- [ ] Legal and commercial: confirm the suspension policy (day +30, open cases unaffected) against tenant contracts and institution rules.
- [ ] Four-eyes thresholds for refunds per currency (proposed INR 50,000 / S$1,000 / US$1,000).
- [ ] Is card surcharging of parties ever permitted per region?
- [ ] Bank statement import: in Odoo (proposed) or in the platform?

### 10.4 [Revenue reporting hooks for finance](../specs/BIL/BIL-revenue-reporting-hooks-for.md)

- [ ] Finance to supply the chart of accounts and posting rules per entity (placeholders above).
- [ ] Deferred revenue schedules: generated by the ledger (proposed) or by the platform?
- [ ] Reporting currency and FX source for group MRR / ARR.
- [ ] Month-end cut-off and accrual policy for late usage.
- [ ] Are intercompany charges between NTPL, TAPL and the US entity ever generated from platform data? Proposed: out of scope.

## 11 Observability (instrumentation layer)

### 11.1 [Foundations](../specs/OBS/OBS-foundations.md)

- [ ] Confirm the `nomo.*` prefix for custom attributes and whether `nomo.user.id` is acceptable as a pseudonymous identifier under DPDP and GDPR (it is still personal data in law if linkable).
- [ ] Tail-sampling rate (10% proposed) and whether two-tier collectors are needed at launch volume.
- [ ] Does any third-party provider (SMS, WhatsApp, video, AI) accept `traceparent`, and should we send it?
- [ ] Telemetry backend per region (shared open question with [[OBS]]).
- [ ] Is 180-day archive needed outside India, or should Singapore and US keep 30 days to minimise data?

### 11.2 [Business events](../specs/OBS/OBS-business-events.md)

- [ ] Final event list per domain (this catalogue is indicative).
- [ ] Should `claim.value_band` bands be defined per tenant / currency, and who owns the band table?
- [ ] Is a separate event stream (for example Kafka-compatible) needed later, or is outbox → Reporting enough?
- [ ] Which events feed aggregator reports (for example SEBI ODR status to NSE, [[RPT-example]]) and need stricter delivery guarantees?

### 11.3 [Performance](../specs/OBS/OBS-performance.md)

- [ ] Confirm SLO targets with product leads and check against client SLAs (SLOs must be stricter than SLAs).
- [ ] Which client contracts include tenant-specific performance commitments that need separate tracking?
- [ ] eBundle and OCR size limits used in the SLIs — match product limits?
- [ ] Who signs the error budget policy (CTO and product lead proposed)?

### 11.3.1 [Frontend real-user monitoring and error reporting](../specs/OBS/OBS-frontend-real-user-monitoring.md)

- [ ] DPO to confirm whether RUM needs consent or notice in each region.
- [ ] Is the hearing media quality sampling acceptable to institutions, or should it be opt-in per tenant?
- [ ] Do we need a separate RUM path for the sandboxed document viewer origin ([[APP-document-viewer-and-sandbox]])?

### 11.4 [Usage](../specs/OBS/OBS-usage.md)

- [ ] DPO: is pseudonymous product analytics covered by our notices in each region, or does it need consent?
- [ ] Do tenants want usage reports for their own users (for example secretariat productivity), and is that acceptable under employment and privacy rules in their jurisdiction?
- [ ] Which features are registered for `nomo.feature.used` at launch?

### 11.5 [Security events](../specs/OBS/OBS-security-events.md)

- [ ] SIEM choice per region (must store in-region).
- [ ] Is the cloud provider's time sync acceptable for CERT-In clock synchronisation in India, or do we configure NIC / NPL NTP sources?
- [ ] Two-year retention for security logs: confirm with legal and ISMS policy.
- [ ] Do client contracts require us to share security events or notify them of specific detections within set times?
- [ ] Who staffs security on-call outside India business hours?

### 11.6 [AI usage](../specs/OBS/OBS-ai-usage.md)

- [ ] Which AI features are in scope at Phase 6, and their final `nomo.ai.feature` keys?
- [ ] Is `edit_ratio` an acceptable quality signal for neutrals, or is it seen as monitoring judges' work? (Needs product and governance view.)
- [ ] Do tenants see their own AI quality signals, or only usage and cost?
- [ ] Price table owner and update process.

### 11.7 [Alerting](../specs/OBS/OBS-alerting.md)

- [ ] On-call and incident tool choice; it receives only alert metadata — confirm that a global SaaS tool is acceptable to legal.
- [ ] On-call model: one 24×7 rotation from Bangalore, or regional rotations once US / Singapore staff exist?
- [ ] Who signs the error budget policy for CORD, TERES and HKIAC CMP?
- [ ] Do client contracts require incident notifications within set times (for example HKIAC or SEBI-regulated tenants)? To be confirmed by legal and account owners.
- [ ] Should tenant admins be able to subscribe to platform incident notifications for their region?

### 11.8 [Uptime / synthetic monitoring](../specs/OBS/OBS-uptime-synthetic-monitoring.md)

- [ ] Status page provider and domain; per-tenant private status pages needed for any client?
- [ ] Should uptime be published per region and product, or per product only?
- [ ] Is the 99.9% monthly uptime SLO consistent with existing client contracts (CORD, TERES, HKIAC CMP)?
- [ ] External probe vendor with nodes in India, Singapore and the US.

## 12 Reporting and Analytics (consumption layer)

### 12.1 [Platform stats](../specs/RPT/RPT-platform-stats.md)

- [ ] Default reporting time zone where a tenant has seats in several countries
- [ ] Is a platform-wide "your figures versus platform median" benchmark wanted for tenants; if so, minimum comparison group size
- [ ] Which reports are in the first release for the arbitral institution tenant versus the SEBI ODR institution tenant

### 12.1.1 [Cases](../specs/RPT/RPT-cases.md)

- [ ] Confirm the terminal status list and whether `on_hold` pauses stage age per rule set
- [ ] Should claim value bands be tenant-configurable, and in which currencies
- [ ] Does a SEBI ODR institution tenant want breach tracking against the circular timelines specifically; if so, legal must confirm the timelines and the rule set must encode them
- [ ] Is "client" for CORD tenants the referring organisation or the claimant

### 12.1.2 [Neutrals](../specs/RPT/RPT-neutrals.md)

- [ ] Does any tenant want individual neutral timeliness used in appointment decisions? If yes, needs privacy and fairness review and a notice to neutrals
- [ ] Are neutral fees invoiced to parties by the tenant or by Nomology for any tenant (affects which billing entity's ledger is the source)
- [ ] Default N days for NEU-M4

### 12.1.3 [Transcribers](../specs/RPT/RPT-transcribers.md)

- [ ] Service-level catalogue (same-day, 24 h, 72 h) and whether targets are per tenant contract
- [ ] Are transcriber quality scores shared with the transcriber, and is there an appeal path
- [ ] Error category list for TRN-M6

### 12.1.4 [Documents](../specs/RPT/RPT-documents.md)

- [ ] Do recordings and transcripts count toward storage entitlement (pricing decision)
- [ ] Should DOC-M9 be a tenant self-service export, or only on request through support

### 12.2 [Compliance reports](../specs/RPT/RPT-compliance-reports.md)

- [ ] Legal to confirm or reject every `assumed` row, with clause references
- [ ] Who owns the register (proposed: Nomology compliance lead, with CTO as technical owner)
- [ ] Are tenants shown the register rows that concern them, as a service

### 12.2.1 [Statutory](../specs/RPT/RPT-statutory.md)

- [ ] Is an internal compliance tenant per region the right container, or should statutory work live outside the product entirely
- [ ] Named officer per entity for each filing

### 12.2.1.1 [Privacy regulator notifications and filings](../specs/RPT/RPT-privacy-and-confidentiality.md)

- [ ] Confirm fiduciary / processor allocation per product and tenant type, and update DPAs
- [ ] Confirm the Board's notification channel and form under the DPDP Rules
- [ ] US state matrix (which states, thresholds, regulator notices) for the US entity's users
- [ ] Contractual notice windows promised to tenants (some institutional clients may require shorter windows than law)
- [ ] Evidence retention period

### 12.2.1.2 [AML, KYC, sanctions screening](../specs/RPT/RPT-aml-kyc-sanctions-screening.md)

- [ ] Counsel: confirm that no Nomology entity is a reporting entity under PMLA (India) or equivalent, and under what business change that would flip
- [ ] US counsel: OFAC duties for the US entity (blocking and reject reporting, timelines)
- [ ] India / Singapore counsel: duties on a confirmed match to UN / MHA / Singapore designations
- [ ] Which tenants require screening records and in what form
- [ ] Retention period for screening records

### 12.2.1.3 [FEMA reporting](../specs/RPT/RPT-fema-violations.md)

- [ ] Finance / CA: list the FEMA filings NTPL actually makes, their deadlines and which need platform data
- [ ] Rename the node to reflect that it supports filings rather than reports violations
- [ ] Should this extract live in the accounting system rather than the platform

### 12.2.2 [Regulatory and Aggregator Reporting](../specs/RPT/RPT-regulatory-and-aggregator.md)

- [ ] Retention minimum for submission evidence
- [ ] Should Nomology ever hold tenant credentials for recipient portals, or only for API / SFTP channels
- [ ] Who at Nomology is second-line reviewer for tenant submissions, if anyone (the tenant owns the obligation)

### 12.2.2.1 [Regulators](../specs/RPT/RPT-regulators.md)

- [ ] Legal: confirm that SEBI ODR reporting by our ODR institution tenants is only to MIIs, and whether any report goes directly to SEBI
- [ ] Are any prospective tenants RBI- or IRDAI-regulated entities that would need regulator-shaped reports from us
- [ ] Owner of the quarterly circular watch

### 12.2.2.2 [Aggregators](../specs/RPT/RPT-aggregators.md)

- [ ] Which aggregators beyond NSE are expected in the next 12 months (other MIIs such as BSE, CDSL, NSDL for SEBI matters; MSME)
- [ ] Is reporting to all MIIs identical, or does each MII have its own format

### 12.2.2.2.1 [SEBI ODR status report to NSE](../specs/RPT/RPT-example.md)

- [ ] Obtain NSE's current format, version and the clause requiring it; replace the provisional field list
- [ ] Is reporting by periodic file, by per-matter updates on the common ODR portal, or both
- [ ] Frequency and due date
- [ ] Do the other MIIs (BSE, CDSL, NSDL) require the same report for matters they allot
- [ ] Rule-set timelines to flag delay (legal to confirm against the circular)

### 12.2.2.2.2 [MSME reporting format](../specs/RPT/ADR-reporting-formats-for-msme-and.md)

- [ ] Identify the MSME aggregator and its reporting recipient (CORD product / founders)
- [ ] Obtain the format, version and legal or contractual source
- [ ] Confirm who reports: tenant or Nomology
- [ ] Rename this node (its ID starts with `ADR-` but it uses the regulatory template); propose title "MSME aggregator reporting format" under [[RPT-aggregators]]

### 12.2.2.4 [Accessibility audit evidence for SEBI-regulated tenants](../specs/RPT/RPT-accessibility-audit-evidence-for.md)

- [ ] Legal: extract exact obligations, deadlines and report contents from the July 2025 circular and the September 2025 guidelines, and any later extension circulars
- [ ] Does the circular reference WCAG 2.2, WCAG 2.1, GIGW or IS 17802, and which applies to our pages
- [ ] Is one platform-wide audit acceptable to tenants, or does each regulated tenant need an audit of its own configuration and branding
- [ ] Budget and appointment of an IAAP-certified external auditor

### 12.3 [MIS and miscellaneous](../specs/RPT/RPT-mis-and-miscellaneous.md)

- [ ] Where the MIS store lives (see [[RPT-report-infrastructure]]) and whether aggregated rows from India-region tenants may be read from Singapore or US
- [ ] Small-count suppression threshold (proposed: 5)

### 12.3.1 [Internal MIS](../specs/RPT/RPT-internal-mis.md)

- [ ] Exchange-rate source and date convention for converted totals (finance)
- [ ] Financial years for TAPL and the US entity
- [ ] Is MIS-M9 cost per case useful or misleading for pricing (HKIAC CMP-style bespoke work skews it)

### 12.3.2 [Industry / marketing](../specs/RPT/RPT-industry-marketing.md)

- [ ] Confirm what GAR or other surveys actually ask for and whether Nomology or the tenant is the respondent
- [ ] Public category list for disputes
- [ ] Do any tenant contracts forbid use of their aggregated data in Nomology marketing even when not identifiable

### 12.4 [Platform performance](../specs/RPT/RPT-platform-performance.md)

- [ ] Which SLOs are contractual per client, and does maintenance count as downtime
- [ ] Do tenants receive the SLA report automatically or on request
- [ ] Retention of daily performance aggregates (proposed 3 years)

### 12.5 [Platform security](../specs/RPT/RPT-platform-security.md)

- [ ] Which incident details tenants see, and how this aligns with contractual incident notices
- [ ] Is the SIEM per region or central (affects residency of security logs)

### 12.6 [AI usage analytics](../specs/RPT/RPT-platform-ai-usage-analytics.md)

- [ ] Is AI cost shown to tenants in money or only in tokens / credits (pricing decision with [[BIL-plans-entitlements-and-usage]])
- [ ] Which quality signals the AI governance owner needs for ISO 42001 monitoring evidence ([[AI-ai-governance-and-impact]])

### 12.7 [Report infrastructure](../specs/RPT/RPT-report-infrastructure.md)

- [ ] ADR: Postgres reporting instance with dbt versus a columnar store (ClickHouse / Redshift / Synapse) per region; recommendation is Postgres first
- [ ] Logical replication from the primary versus CDC through Debezium; logical replication is simpler but couples schema changes
- [ ] Where the internal MIS store lives and which region hosts it; whether some tenants' contracts forbid even aggregated rows leaving the region
- [ ] Evidence retention period per obligation (drives object lock duration); needs legal input from [[RPT-compliance-reports]]
- [ ] Is a dashboard library (embedded BI) acceptable, or are dashboards built with our own components and [[PKG-data-visualisation-palette]]?

## 13 Security and Compliance (controls)

### 13.1 [ISMS controls](../specs/SEC/SEC-isms-controls.md)

- [ ] Confirm ISMS scope: does the first certificate include the US entity and Azure deployments?
- [ ] Is the Privacy category in the first SOC 2 report, or Security, Availability and Confidentiality only?
- [ ] GRC tooling: spreadsheet register for Phase 1, or a compliance automation platform? (Affects automation target.)
- [ ] Internal auditor: in-house with independence safeguards, or outsourced?
- [ ] Merged item "ISO 27001, SOC 2" (from the former Security node) is now covered by Objective and Mapping; remove after review.

### 13.2 [Privacy controls](../specs/SEC/SEC-privacy-controls.md)

- [ ] Confirm Nomology's role per product and tenant type (especially CORD and SEBI ODR tenants). Owner: legal.
- [ ] Confirm which DPDP exemptions (s.17(1)(a) legal claims; s.17(1)(b) judicial / quasi-judicial bodies) apply to arbitration and ODR processing. Owner: legal.
- [ ] Dates from which the DPDP Rules' substantive obligations apply (Rules 3 and 5–16 commence eighteen months after publication) [R2]; plan to be compliant before then.
- [ ] Is a GDPR Art. 27 EU representative needed (EU parties in arbitrations where Nomology is controller)?
- [ ] Which US state laws apply given thresholds (likely few, as Nomology is mainly a processor for US tenants)?

### 13.2.1 [Consent and notice management](../specs/SEC/SEC-consent-and-notice-management.md)

- [ ] Legal bases per journey (table above) to be confirmed by legal, especially reliance on the legal-claim exemption.
- [ ] Which Eighth Schedule languages must notices be available in at launch for SEBI ODR and CORD tenants? Proposed: English and Hindi first, then tenant-requested languages.
- [ ] Consent manager integration: required by any tenant? Revisit after Rule 4 commences.
- [ ] Retention period for consent records (7 years proposed).

### 13.2.2 [Data principal rights requests](../specs/SEC/SEC-data-principal-rights-requests.md)

- [ ] Statutory response periods for DPDP access, correction and erasure (beyond the 90-day grievance limit) — legal to confirm and set in the published policy.
- [ ] Identity verification for unrepresented parties without accounts (SEBI ODR investors): is matching case reference plus OTP to the registered phone enough? DPO to decide.
- [ ] What an access request returns from case records: the person's own data only, or case documents they are entitled to as a party anyway? Proposed: personal data summary plus pointers to case documents already available to them.
- [ ] Appeal window length (30 days proposed).
- [ ] Whether tenants want the workflow to send responses in their name (white-label) when they are the fiduciary.

### 13.2.3 [Privacy notice copy](../specs/SEC/SEC-privacy-notice-copy.md)

- [ ] Legal to confirm the exact DPDP Rule 3 notice elements and whether a consent-manager reference is required.
- [ ] Which languages are required at launch for SEBI ODR and CORD tenants?
- [ ] Does each institution want its own full notice (tenant-authored) or our template with its details?
- [ ] Who in Nomology is named as Grievance Officer / DPO in the Nomology-as-fiduciary notice?

### 13.3 [Data classification](../specs/SEC/SEC-data-classification.md)

- [ ] Do institutional rules (for example confidentiality provisions in an institution's arbitration rules) require additional tiers? To be checked per tenant during onboarding.
- [ ] Should the default tier for uploaded evidence be "case participants" for all tenant types, or tenant-configurable?
- [ ] Which data types are "sensitive personal" for DPDP purposes (the Act has no special-category list, unlike GDPR)? Proposed: use the GDPR list plus financial and identity data; DPO to confirm.

### 13.4 [Vulnerability management](../specs/SEC/SEC-vulnerability-management.md)

- [ ] Select SAST and DAST tools (budget and self-hosting needs).
- [ ] Do any client contracts require sharing pen test summaries or allowing client-led tests? Collect during onboarding.
- [ ] Public bug bounty or private disclosure programme only? Proposed: private disclosure first.

### 13.5 [Access reviews](../specs/SEC/SEC-access-reviews.md)

- [ ] Choose the just-in-time tool for infrastructure access (cloud-native, or a dedicated access broker); application JIT is built in ([[PKG-jit-and-break-glass]]). (Platform lead)
- [ ] Confirm DPDP Rules 2025 rule number for reasonable security safeguards. (Legal)
- [ ] Should tenant campaigns include external parties and counsel on open cases by default for court programmes? (Product)

### 13.6 [Vendor / sub-processor management](../specs/SEC/SEC-vendor-sub-processor-management.md)

- [ ] Standard sub-processor change notice period (30 days proposed) versus what institutional client contracts require.
- [ ] Do any SEBI-regulated tenants or MIIs require prior approval (not just notice) for sub-processor changes? To be confirmed per client.
- [ ] Legal view on transfers of Indian personal data under DPDP s.16 (currently a negative-list approach; no list notified at the time of writing — assumption, to be confirmed by legal).

### 13.7 [Security incident response and breach notification](../specs/SEC/SEC-security-incident-response-and.md)

- [ ] Confirm fiduciary / processor role per product (TERES for institutions, CORD, enterprise) — determines who notifies the DPDP Board and data principals.
- [ ] Contractual tenant notification deadline: 24 hours proposed; check against institutional client contracts.
- [ ] SEBI-related reporting duties for incidents affecting SEBI ODR matters (through MIIs) — legal to confirm.
- [ ] Which person is designated CERT-In point of contact for NTPL?
- [ ] Do we need a retained forensic firm on contract per region?

### 13.8 [Business continuity](../specs/SEC/SEC-business-continuity.md)

- [ ] Confirm RTO / RPO targets with operations and against client SLAs.
- [ ] Which regions have a second in-country cloud region available, and is a second Indian region used for DR? Owner: DevOps.
- [ ] Do institutional clients accept read-only offline exports during prolonged region loss, and under what controls?
- [ ] Should outage certificates be a product feature in Phase 7?

## 14 Infrastructure

### 14.1 [Cloud and IaC](../specs/INF/INF-cloud-and-iac.md)

- [ ] Terraform (BSL licence) or OpenTofu? Do any client contracts or our licence review constrain this?
- [ ] Confirm GitHub Actions as the CI system and GitHub OIDC as the identity for applies.
- [ ] Are non-production environments only in India, or does each region need its own staging for client UAT with regional data?
- [ ] Which IaC tool for Azure: Terraform `azurerm` (proposed, one toolchain) or Bicep if a client's team must maintain it?
- [ ] Who are the CODEOWNERS for `infra/` and who may approve production applies?

### 14.2 [Compute](../specs/INF/INF-compute.md)

- [ ] Node.js 24 LTS for all workloads — any library (Temporal SDK, Prisma engines, sharp) not yet supported on it or on ARM64?
- [ ] Should the `ai-pipelines` worker run GPU or large-memory tasks (local OCR / transcription models), or are all heavy models called through the AI gateway?
- [ ] Do we need a separate `web-public` service for public filing and status pages so a spike there cannot starve signed-in users?
- [ ] Final task-size numbers after the first load test.

### 14.3 [Orchestration](../specs/INF/INF-orchestration.md)

- [ ] Fargate only, or EC2 capacity providers for Temporal history / AI workers where per-vCPU cost matters?
- [ ] Is CodeDeploy blue/green needed from day one, or is rolling plus circuit breaker enough until Phase 8?
- [ ] For Azure clients: is Container Apps enough for Temporal server services, or would they run on a VM scale set / AKS?
- [ ] Is ECS Service Connect acceptable for Temporal's internal membership, or should Temporal services use static internal NLBs?

### 14.4 [Temporal](../specs/INF/INF-temporal.md)

- [ ] Confirm 1,024 history shards per production cluster (cannot be changed later).
- [ ] Visibility store: Postgres advanced visibility vs OpenSearch per region (shared open question with [[WF-separation-of-concerns-temporal]]).
- [ ] Namespace retention for closed workflows: 30 days enough for support investigations?
- [ ] Do non-production namespaces share one cluster in India, or does each environment get its own cluster?
- [ ] Who owns Temporal upgrades and on-call: platform engineering or a dedicated SRE role?
- [ ] For Azure clients, where does Temporal run (Container Apps vs VMs), and is Temporal Cloud ever acceptable?

### 14.5 [Redis](../specs/INF/INF-redis.md)

- [ ] ElastiCache engine: Valkey or Redis OSS? Confirm BullMQ compatibility of the chosen engine version in staging.
- [ ] Azure: confirm Azure Managed Redis as the target service and its availability in the Azure regions we need.
- [ ] Which BullMQ queues carry jobs that are not backed by an outbox row, and is that loss acceptable?
- [ ] Should rate-limit counters move to the cache Redis so queue memory is reserved for jobs?

### 14.6 [Database](../specs/INF/INF-database.md)

- [ ] RDS for PostgreSQL or Aurora PostgreSQL? (Proposed ADR.)
- [ ] PostgreSQL 17 or 18 at launch?
- [ ] Does the RAG vector store live in this database (pgvector) or in a separate store ([[AI-rag]])?
- [ ] Reporting: is one in-region read replica enough, or is a warehouse needed from Phase 7 ([[RPT-report-infrastructure]])?
- [ ] Confirm maintenance windows per region against hearing schedules of the largest tenants.
- [ ] Is IAM database authentication acceptable for the migration and admin roles on both AWS and Azure (Entra ID auth)?

### 14.7 [Database connection handling](../specs/INF/INF-database-connection-handling.md)

- [ ] Confirm the Prisma major version (v6 URL parameters vs v7 driver-adapter pool settings) in [[APP-framework-dependencies]].
- [ ] Do any workloads need session features (advisory locks for singleton jobs, LISTEN/NOTIFY)? If so, they need a separate direct, session-mode connection profile.

### 14.7.1 [PgBouncer](../specs/INF/INF-pgbouncer.md)

- [ ] Accept self-run PgBouncer on ECS for AWS (proposed), or test RDS Proxy despite the pinning behaviour?
- [ ] Should PgBouncer run as a sidecar per `web` task instead of a central service? (Simpler networking, but multiplies server pools and weakens the budget.)
- [ ] Is a separate pooler needed in front of the reporting replica, or do reporting jobs connect directly with a small pool?

### 14.8 [Networking](../specs/INF/INF-networking.md)

- [ ] Is a global CDN acceptable to clients and under DPDP / PDPA for pass-through traffic (TLS terminates at edges outside the region), or must some tenants use a regional ALB with no CDN?
- [ ] Do large document downloads go through signed S3 URLs directly or through the CDN with signed cookies?
- [ ] AWS Shield Advanced: needed for any client SLA?
- [ ] Product domains per product (CORD, TERES) and per region — final naming scheme for tenant subdomains.

### 14.9 [Secrets and keys](../specs/INF/INF-secrets-and-keys.md)

- [ ] Do any institutions (for example arbitral institutions or SEBI-regulated tenants) require customer-managed or customer-held keys (BYOK / HYOK) for their documents? This would need per-tenant KMS keys and changes to the storage and field encryption design.
- [ ] HSM-backed keys (AWS CloudHSM / Azure Managed HSM) required by any contract or audit?
- [ ] Rotation period for database credentials: 30 days proposed — agree with ISMS policy ([[SEC-isms-controls]])?

### 14.10 [Backup and disaster recovery](../specs/INF/INF-backup-and-disaster-recovery.md)

- [ ] Approve in-country DR regions: India → ap-south-2 Hyderabad, US → us-west-2. Any client or legal reason against?
- [ ] Choose the Singapore region-loss option (multi-AZ only, Azure Southeast Asia standby, or lawful copy abroad) and confirm with legal under PDPA.
- [ ] Are the proposed region-loss targets (RPO 15 min / RTO 8 h) acceptable to institutions with hearing schedules, and what do client contracts promise today?
- [ ] Backup retention vs deletion obligations under DPDP and GDPR: is 12 months of monthly snapshots acceptable with deletion replay? (To be confirmed by legal / DPO.)
- [ ] Who declares a region disaster and approves failover?

## 15 Deployment and Release

### 15.1 [CI/CD pipelines (build, test, scan, deploy)](../specs/DEP/DEP-ci-cd-pipelines-build-test.md)

- [ ] Confirm GitHub Actions as CI platform (assumed throughout) and whether self-hosted runners are needed for any job.
- [ ] Coverage thresholds: per package or global? Proposal in [[TST-unit-integration-contract-and]].
- [ ] Do we target SLSA build level 3 (hardened builder) for audit, or is level 2 sufficient for client questionnaires?
- [ ] How long are build logs, SBOMs and attestations retained for audit evidence?

### 15.2 [Preview environments per PR](../specs/DEP/DEP-preview-environments-per-pr.md)

- [ ] Terraform per preview or a scripted ECS approach? Terraform is consistent but slower to create.
- [ ] Is a shared Temporal namespace acceptable, or do we need per-PR namespaces for workflow-versioning tests?
- [ ] Budget ceiling for previews per month.
- [ ] Do previews need an Azure variant, or is staging-az enough for Azure-specific changes?

### 15.3 [Database migration strategy (zero-downtime)](../specs/DEP/DEP-database-migration-strategy-zero.md)

- [ ] Confirm the exact Prisma Migrate behaviour for `CREATE INDEX CONCURRENTLY` in a single-statement migration with the Prisma version chosen in [[APP-framework-dependencies]].
- [ ] Confirm `lock_timeout` and `statement_timeout` values after the first rehearsal on production-sized data.
- [ ] How long must a contract step wait for long-running Temporal workflows? Needs a payload versioning rule ([[DEP-blue-green-canary-releases]]).
- [ ] Should backfills that touch every tenant need tenant notice when they run for hours?

### 15.4 [Blue-green / canary releases, rollback](../specs/DEP/DEP-blue-green-canary-releases.md)

- [ ] ECS built-in blue/green or CodeDeploy? Settle by ADR before Phase 3.
- [ ] Retirement policy for old Temporal worker versions when cases stay open for years: force Continue-As-New onto the new version after N releases?
- [ ] Source of protected-window data: hearings schedule plus a tenant-maintained calendar in [[PKG-settings]]?
- [ ] Canary thresholds to be tuned after the first months of real traffic.

### 15.5 [Release notes and change management](../specs/DEP/DEP-release-notes-and-change.md)

- [ ] Which client contracts require advance notice of changes or maintenance, and how long? (Legal to confirm per client.)
- [ ] Is a weekly train right for all regions, or should regulated tenants (SEBI ODR institutions) get a slower cadence?
- [ ] Retention period for change records as audit evidence.
- [ ] Do tenant-facing notes need translation into tenant languages at launch?

### 15.6 [Environment promotion and multi-region rollout](../specs/DEP/DEP-environment-promotion-and-multi.md)

- [ ] Confirm the wave order rule with product and client success, including which region is wave 1 in practice.
- [ ] Bake time: 24 hours for all releases, or shorter for standard releases with no migrations?
- [ ] Does each Azure client deployment need its own UAT, and who approves production for it (client sign-off required by contract)?
- [ ] Release windows by time zone: a single global window or per region (India IST, Singapore SGT, US Eastern)?

## 16 Testing and Quality

### 16.1 [Unit, integration, contract and end-to-end tests (Playwright)](../specs/TST/TST-unit-integration-contract-and.md)

- [ ] Confirm changed-line coverage threshold (80% proposed) and whether domain packages need a higher one.
- [ ] Property-based OpenAPI testing tool choice (Schemathesis is Python; acceptable in CI?).
- [ ] Which aggregators (for example NSE for SEBI ODR matters) would participate in consumer-driven contract testing, if any?
- [ ] Browser matrix for e2e: all three engines on every staging run, or WebKit nightly only?

### 16.2 [Multi-tenant isolation tests (cross-tenant data leak checks)](../specs/TST/TST-multi-tenant-isolation-tests.md)

- [ ] Should missing tenant context raise an error (policy uses `current_setting('app.tenant_id')` without `missing_ok`) everywhere? Proposed yes; confirm against the policy text in [[MT-rls-enabled-and-forced-on]].
- [ ] Is a production read-only catalogue check after each migration acceptable to the information security owner (it uses the reporting role)?
- [ ] How are isolation tests run for Azure deployments where PgBouncer is the Flexible Server built-in ([[INF-pgbouncer]])?

### 16.3 [Performance and load testing](../specs/TST/TST-performance-and-load-testing.md)

- [ ] Forecast peak volumes per region and tenant type (tenants, cases per month, concurrent hearings, aggregator batch sizes) from product and client success.
- [ ] Are the proposed latency targets consistent with client SLAs?
- [ ] Do we need a dedicated performance environment, or scale staging temporarily?
- [ ] Azure deployments: run the same scenarios before each Azure client goes live?

### 16.4 [Security testing](../specs/TST/TST-security-testing.md)

- [ ] Assumption: SEBI-regulated tenants (through their MII) may require security audits by a CERT-In empanelled auditor; legal and the tenant to confirm, and whether our pen test can serve as that evidence.
- [ ] Do arbitral institution clients (for example under security schedules in their contracts) require sharing pen test summaries? Legal to confirm per contract.
- [ ] ASVS Level 2 for all surfaces, or Level 3 for platform admin and authentication?
- [ ] Bug bounty or responsible disclosure programme: when?

### 16.5 [Accessibility testing](../specs/TST/TST-accessibility-testing.md)

- [ ] Who is the accessibility lead and who performs the yearly specialist audit?
- [ ] Does any SEBI-regulated tenant require the audit to be by an IAAP-certified professional? (Assumption based on the node title of [[RPT-accessibility-audit-evidence-for]]; legal to confirm against the current SEBI circular.)
- [ ] Budget and recruitment route for testing with disabled users in India, Singapore and the US.
- [ ] Do we test Indic-language screen-reader output (for example Hindi with NVDA) before launching those locales?

### 16.6 [Evals and AI testing](../specs/TST/TST-evals-and-ai-testing.md)

- [ ] Which tenants, if any, will consent to anonymised case material for eval sets, and under what contract terms?
- [ ] Confirm the proposed thresholds with legal reviewers after the first baseline runs.
- [ ] Eval harness: build in-house, or adopt an open-source runner (for example promptfoo) wrapped in our CI?
- [ ] Is the EU AI Act relevant for any tenant serving EU-based parties? Annex III lists AI used in alternative dispute resolution among high-risk uses [R5]; legal to assess per feature.
- [ ] Retention period for eval outputs that include anonymised case-derived text.

## 17 Documentation and Developer Experience

### 17.1 [Architecture docs and runbooks](../specs/DOC/DOC-architecture-docs-adrs-runbooks.md)

- [ ] Structurizr DSL or Mermaid as the diagram standard?
- [ ] Where do client-specific Azure deployment diagrams live, given contract confidentiality?
- [ ] Who runs game days, and are clients invited to observe DR exercises?

### 17.2 [API documentation (OpenAPI, developer portal)](../specs/DOC/DOC-api-documentation-openapi.md)

- [ ] Public or authenticated developer portal? Proposal: public reference, authenticated sandbox and aggregator-specific guides.
- [ ] API versioning style (path `/v1` vs header) to confirm with [[APP-api-versioning-rate-limiting]].
- [ ] Do we publish SDKs (TypeScript first) generated from OpenAPI?

### 17.2.1 [Developer-facing API copy](../specs/DOC/DOC-developer-facing-api-copy.md)

- [ ] Do any aggregators or institutions need API error text in a language other than English?
- [ ] Should the `wrong-region` problem reveal the correct region URL, or is that itself information about the tenant? (Proposal: yes, because the client is already authenticated to that tenant.)
- [ ] Legal to confirm wording for filing timestamp and deemed receipt descriptions per tenant type.

### 17.3 [Onboarding guide for engineers](../specs/DOC/DOC-onboarding-guide-for-engineers.md)

- [ ] Training provider and record system for ONB-4.
- [ ] Is 30 days the right delay for production access, and who approves earlier access for senior hires?
- [ ] Do contractors from third-party firms use our laptops or their own (device management requirement)?

### 17.4 [Tenant-facing help centre](../specs/DOC/DOC-tenant-facing-help-centre.md)

- [ ] Content source: MDX in the repo (versioned with code) or a headless CMS (editable by product and tenant admins without deploys)?
- [ ] Is the contact form in scope for phase 1, or do tenants use their own support channels?
- [ ] Which languages are required at launch for each tenant? (See [[I18N-l10n]].)
- [ ] Should search be served by the platform search package ([[PKG-search]]) or a static index per locale?

### 17.4.1 [Plain-language guidance for unrepresented parties](../specs/DOC/DOC-plain-language-guidance-for.md)

- [ ] Confirm reading targets with product and legal.
- [ ] Confirm the procedural description for SEBI ODR matters (conciliation and arbitration stages) against the current SEBI circular and each ODR institution tenant's rules.
- [ ] Which languages are needed for MSME claimants at launch?
- [ ] Recruitment route for comprehension testing participants (investors, MSMEs) in each language.

## 18 Order of Implementation

### 18 [Order of Implementation](../specs/PLAN/PLAN.md)

- [ ] Target dates per phase and the pilot tenant: who and when?
- [ ] Is migration of existing CORD and TERES tenants a separate plan node (proposed), and which phase must be complete before the first migration?
- [ ] Which certifications and reports are required, by which entity, and by when (ISO 27001 scope, SOC 2 Type I or Type II)? This sets when the observation period must start.
- [ ] Which region hosts the pilot tenant, and does it need Azure?
- [ ] Capacity: team size and allocation per phase after support load; not yet stated.
- [ ] Should Phase 6 (AI) start in parallel with Phase 4 or 5 once Phase 3 document events exist? Proposed: yes for gateway and governance work, features only after Phase 4.

## 19 Decisions

### 19.9 [Expression and rules language](../specs/ADR/ADR-expression-and-rules-language.md)

- [ ] Accept CEL (Option A) over the in-house grammar (Option F), accepting a dependency on a community JavaScript implementation for a published specification? (CTO)
- [ ] Accept evaluation in the browser for previews and form feedback, with the server as the authority? This changes [[WF-workflow-authoring-studio]]. (CTO with security)
- [ ] Confirm that DMN XML import and export stay out of scope for launch. (Product)
- [ ] Ownership of the `expr/1` profile and its function list: workflow squad, with security review for each new function? (Platform engineering lead)
- [ ] Form calculations limit: 500 characters, or the same 200 as gateways? (Product)

### 19.10 [Identity platform](../specs/ADR/ADR-identity-platform.md)

- [ ] Risk appetite: accept owning authentication code (with pen tests and certified libraries) rather than running Keycloak as the identity server or paying for three Auth0 Private Cloud deployments. (CTO)
- [ ] Should we obtain an Auth0 Private Cloud quote for India, Singapore and US now, as a priced fallback? (CTO)
- [ ] Do any current or contracted clients require Azure-only hosting or Entra as the identity platform? (CTO, sales)
- [ ] Confirm with Ory in writing which Polis features, if any, need the Ory Enterprise License. (Security)
- [ ] Breached-password check: k-anonymity service or offline corpus per region ([[PKG-email-password-magic-link-otp#questions]]). (Security, DPO)
- [ ] Record the security reviewer and date for this ADR. (Security lead)

### 19.11 [Authorisation policy engine](../specs/ADR/ADR-policy-engine.md)

- [ ] Accept that assurance rests on generated and mutation tests rather than formal policy analysis (Cedar), at least until the revisit triggers fire. (CTO)
- [ ] Will tenants ever author authorisation rules themselves (beyond roles, sets, scopes and settings)? This is the main trigger for a policy language. (CTO, product)
- [ ] Does any bespoke or partner deployment (for example the HKIAC case management platform) need to call our decisions from outside the TypeScript monorepo in the next 18 months? If yes, schedule the AuthZEN endpoint. (CTO)
- [ ] Agree the mutation-testing threshold and the spike's effort criterion. (Security lead)
- [ ] Should a second RLS policy enforce the `tribunal_only` tier in the database? Kept open in [[PKG-authorization#questions]]; not decided here. (Security lead)
- [ ] Record the security reviewer and date for this ADR. (Security lead)

### 19.12 [Workflow interpreter versioning](../specs/ADR/ADR-workflow-interpreter-versioning.md)

- [ ] Accept the previous-major support window of 24 months for interpreter contracts, or tie it to the longest expected case duration per tenant type (for example 36 months for institutional arbitration)? (CTO)
- [ ] Accept "roll-forward only" as the default rollback policy for interpreter builds? (CTO)
- [ ] Rollover age `workflow.runtime.max_run_age_days`: 30 days proposed. (Workflow squad)
- [ ] Region rollout order and the length of the ramp at 10% (24 hours proposed). (DevOps with product)
- [ ] Do production replay tests use anonymised production histories, or staging only? This affects coverage and the privacy review in [[SEC-privacy-controls]]. (Security)

