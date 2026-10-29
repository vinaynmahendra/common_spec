# Template: Shared package (`package`)

Generated from `package.json`. Edit the JSON, then run `python3 tools/specs.py index`.

**Purpose:** Specifies a reusable internal library in the monorepo (packages/*) that many apps and services import, so its contract is stable and its behaviour predictable.

**Depth:** 3–8 pages. The public API section must be precise enough that a consumer could code against it before it exists. Internals stay brief; link a Design note if they need debate. Split into child nodes when one package has several independent sub-modules (e.g. Notifications → email, SMS, WhatsApp).

**Default child template:** `requirement`

## Sections

Level 1 = Core (needed for review), 2 = Full (needed to approve), 3 = Optional.

### `purpose` Purpose and scope (level 1)

What problem the package solves, who imports it, and what it deliberately does not do.

Illustrative example (not a requirement):

> `@platform/notifications` sends messages to people on behalf of any app (case portal, admin, workers) through one call, picking the channel and template per tenant settings.
> 
> **Does not:** decide *when* to notify (that is the calling workflow's job), or store message content long-term (Audit trail does).

### `consumers` Consumers and use cases (level 1)

Which apps / services call it and for what. 3–6 concrete use cases.

Illustrative example (not a requirement):

> | Consumer | Use case |
> |---|---|
> | Hearing reminder workflow (Temporal activity) | Remind neutral 7 days before hearing |
> | Case portal | Notify parties when a document is filed |
> | Admin app | Notify tenant admins of failed SSO configuration |

### `api` Public API (level 1)

Exported functions, types and events with signatures. This is the contract; everything not listed is internal.

Illustrative example (not a requirement):

> ```ts
> export interface NotifyRequest {
>   tenantId: string;
>   recipients: RecipientRef[];          // user IDs or party IDs, never raw emails
>   template: TemplateKey;               // e.g. 'hearing.reminder'
>   data: Record<string, unknown>;       // template variables
>   channels?: Channel[];                // default: tenant preference order
>   idempotencyKey: string;              // required; duplicates are dropped
> }
> export function notify(req: NotifyRequest): Promise<NotifyResult>;
> export type NotifyResult = { messageIds: string[]; skipped: SkippedRecipient[] };
> ```

### `usage` Usage examples (level 2)

Copy-pasteable snippets for the 2–3 most common calls, including error handling.

Illustrative example (not a requirement):

> ```ts
> await notify({
>   tenantId, template: 'hearing.reminder',
>   recipients: [{ userId: neutralId }],
>   data: { caseRef: 'HKIAC/A24/0193', hearingAt },
>   idempotencyKey: `${tenantId}:hearing-reminder:${hearingId}`,
> });
> ```

### `tenant` Tenant context (level 1)

How tenant context enters (argument, async context, request scope) and what happens if it is missing.

Illustrative example (not a requirement):

> `tenantId` is a required argument. The package re-checks it against the active tenant context from the request / Temporal interceptor and throws `TenantMismatchError` if they differ. Templates and channel settings are loaded per tenant; there is no cross-tenant cache key.

### `config` Configuration (level 2)

Settings, defaults, where they live (env, Settings package, tenant config) and who can change them.

Illustrative example (not a requirement):

> | Setting | Default | Level |
> |---|---|---|
> | `channels.order` | email, sms | Tenant |
> | `quietHours` | none | Tenant |
> | `provider.email` | SES (per region) | Platform (env) |

### `adapters` Providers and extension points (level 2)

Pluggable providers, how to add one, and the interface they implement.

Illustrative example (not a requirement):

> Channels implement `ChannelAdapter { send(msg): Promise<ProviderReceipt> }`. Shipped: SES email, Twilio SMS, WhatsApp Business. Adding one = new adapter + registration + contract tests; no change to callers.

### `errors` Error model (level 2)

Error types, which are retryable, and what callers should do.

Illustrative example (not a requirement):

> | Error | Retryable | Caller action |
> |---|---|---|
> | `TemplateNotFound` | No | Fix template key / tenant config |
> | `ProviderUnavailable` | Yes (backoff) | Let Temporal retry the activity |
> | `RecipientOptedOut` | No | Returned in `skipped`, not thrown |

### `nfr` Performance and limits (level 2)

Latency budgets, throughput, size limits, rate limits.

Illustrative example (not a requirement):

> - `notify()` returns within 200 ms p95 (sending is queued via BullMQ)
> - Max 500 recipients per call; larger batches use `notifyBulk()`
> - Per-tenant send rate capped by plan (Billing entitlements)

### `versioning` Versioning and compatibility (level 2)

Semver policy, deprecation window, how breaking changes are rolled out across the monorepo.

Illustrative example (not a requirement):

> Semver. Breaking changes require a major bump, a codemod or migration note, and one release where the old signature still works with a deprecation warning.

### `testing` Test contract (level 2)

What the package guarantees via tests, and what consumers can rely on.

Illustrative example (not a requirement):

> - Contract tests per adapter against provider sandboxes
> - Idempotency: same key twice → one send
> - Tenant isolation: tenant A templates never resolve for tenant B

### `questions` Open questions (level 3)

Unresolved items as a checklist.

Illustrative example (not a requirement):

> - [ ] Do we need delivery receipts surfaced back into case timelines?

## Checks

### `tenancy` Tenant isolation

**Question:** Can any public function of this package read, write, cache or emit data for a tenant other than the one in the active tenant context, whether through normal use, misuse or a bug?

- Which exported functions take tenantId as an argument, which derive it from the request / Temporal interceptor context, and what exactly happens (error type, log, metric) when the two disagree or the context is missing?
- Does every database call run inside a transaction that sets the tenant with SET LOCAL / set_config(..., true) through the Prisma extension, so the setting cannot leak to the next client on a PgBouncer transaction-pooled connection?
- Does the package ever connect as a role that bypasses Row-Level Security (table owner, BYPASSRLS, superuser)? If a platform-admin path needs cross-tenant reads, how is it separated, named and audited?
- Are all Redis keys, BullMQ queue/job names, object-storage paths, search indexes and in-process caches prefixed or partitioned by tenant (and region), and is that enforced in one helper rather than by each caller?
- Can a caller pass raw identifiers (user IDs, document IDs, email addresses) that belong to another tenant, and does the package verify ownership before acting on them?
- Is tenant context carried correctly across async boundaries the package creates (BullMQ jobs, Temporal activities, timers, streams), or could a background task run with no tenant or the wrong one?
- Is there a platform-level (non-tenant) mode, and how is it prevented from being used accidentally by app code?

**Good answer:** Names the single mechanism by which tenant context enters (argument plus context cross-check) and the error thrown when it is missing or mismatched. Shows that every storage the package touches (Postgres under forced RLS, Redis, object storage, search, caches) is partitioned by tenant through one shared helper, and that no code path uses an RLS-bypassing role except a separately named, audited admin path. Points to automated cross-tenant tests that try to read tenant B's data while acting as tenant A and expect a denial.

**Red flags:**

- Tenant filtering relies on callers remembering to add a where-clause, with RLS 'as a backup' not actually forced
- Tenant set with session-level SET (not SET LOCAL) on a PgBouncer transaction-pooled connection
- Cache or Redis keys built without tenant ID, or a shared in-memory cache keyed only by entity ID
- No defined behaviour when tenant context is missing (silently falls back to a default tenant or to no filter)

### `security` Security of the API surface

**Question:** Does the package validate what it is given, hold only the privileges it needs, and keep secrets and dangerous capabilities away from callers?

- Are all public inputs validated at the package boundary with a schema (e.g. zod), including size limits, allowed characters and enum values, with typed errors rather than thrown strings?
- Which credentials does the package need (database role, KMS key, provider API key), where are they loaded from (secrets manager per region, never env files in the repo), and how are they rotated without a redeploy of every consumer?
- What is the database role or IAM policy the package runs under, and is it the minimum (e.g. no DELETE on audit tables, no access to other packages' schemas)?
- Does any function accept free-form strings that end up in SQL, shell commands, file paths, HTML, URLs or template engines? How is injection prevented (parameterised queries, path normalisation, output encoding, SSRF allow-lists)?
- Is the package safe to call from the browser bundle, or server-only? How is accidental client-side import blocked (e.g. 'server-only' import, Turborepo boundaries)?
- Which third-party dependencies does it add, are they pinned via the lockfile, scanned for known vulnerabilities in CI, and reviewed for install scripts?
- For packages that do authorisation (Authentication, Data access), is access denied by default when a permission is not explicitly granted?

**Good answer:** Lists every input entry point with its validation schema and limits, the exact least-privilege role or IAM policy, and the secrets the package uses with their storage path and rotation period. States whether the package is server-only and how that is enforced by tooling. Records the dependency-scanning gate in CI and maps the relevant OWASP ASVS requirements (input validation, secrets, access control) to tests.

**Red flags:**

- Secrets read from process.env with no secrets-manager path or rotation plan
- Package connects with an owner or admin database role 'for simplicity'
- Validation left to the calling app
- A server-only package (holding keys or DB access) importable from client components without a build-time guard

### `data-protection` Personal data handling

**Question:** What personal data passes through or is stored by this package, and does the package make correct handling (minimisation, masking, retention, erasure) the default for every consumer?

- Which fields in the public API are personal data or sensitive case data (names, emails, phone numbers, ID documents, hearing content), and are they typed or tagged so they can be found and masked automatically?
- Does the package log, trace or put into error messages any personal data? Which redaction is applied, and is it on by default?
- If the package stores data, what is the retention period, who sets it (platform or tenant), and how is deletion or anonymisation done to meet DPDP Act / GDPR erasure requests without breaking legal holds on arbitration records?
- Does the package expose a way for the Data subject request process to find and export or erase everything it holds for one person?
- Are fields that need extra protection (e.g. KYC documents, bank details) encrypted at the field level with a tenant- or region-scoped key, and who can decrypt?
- Does the package send personal data to any third party (email/SMS provider, search service, AI model)? If so, is that listed so the integration and vendor checks cover it?

**Good answer:** Contains a short data inventory for the package: each personal-data field, why it is needed, where it is stored, retention, and how it is erased or exported. States that logs and traces redact personal data by default with the redaction helper named. Explains how erasure interacts with legal holds and audit records (for example, pseudonymise the person but keep the procedural record).

**Red flags:**

- Full request payloads logged at info or error level
- No retention period, or 'we keep everything'
- No way to locate one person's data inside the package for a data subject request
- Personal data sent to an external service not listed anywhere

### `residency` Region awareness

**Question:** Does the package always keep a tenant's data and processing in the tenant's pinned region (India, Singapore or US), and fail safely if it cannot?

- How does the package learn the current region (deployment config, tenant record), and what happens if the tenant's region differs from the region of the running service?
- Which regional resources does it use (database, Redis, S3 bucket, KMS key, email provider endpoint, search cluster), and is each one resolved per region rather than hard-coded?
- Can any code path send tenant data to a global or single-region service (a shared analytics store, a US-only provider, a global CDN cache of private content)?
- Do background jobs or Temporal activities started by the package run on the region's own workers and task queues?
- If a regional dependency is unavailable, does the package fail closed (error) rather than fall back to another region?

**Good answer:** States the rule 'tenant data never leaves the pinned region' and shows how the package enforces it: region read from one config source, all resources resolved per region, and a hard error on region mismatch. Lists any data that is deliberately global (for example, non-personal feature-flag definitions) and why it is acceptable.

**Red flags:**

- Falls back to another region's endpoint on error
- Single global bucket, index or queue shared by all regions
- Region chosen by an environment default rather than by the tenant record

### `audit` Audit events

**Question:** Which operations of this package must leave a tamper-evident audit record, and is emitting that record part of the operation rather than an optional extra the caller may forget?

- List each operation that changes state, grants or uses access, reveals sensitive data, or sends something to a person, and mark whether it emits an audit event.
- What does each event contain (actor, on-behalf-of, tenant, region, action, target, before/after or a hash of it, reason, request and trace IDs, timestamp from a trusted clock)?
- Is the audit write in the same database transaction as the change (or written via an outbox), so a change cannot succeed without its audit record?
- Are audit records append-only for the application role, and is there tamper evidence (hash chaining or write-once storage)?
- How long are audit records kept, per regulation and tenant contract (for example arbitration institution rules, SEBI ODR requirements, ISO 27001 evidence), and are they kept in-region?
- Are reads of sensitive data (award drafts, KYC documents) audited, not only writes?

**Good answer:** A table of operations versus audit event type with the event schema, using the shared Audit trail package. Explains the transactional or outbox guarantee, the append-only role and tamper evidence, and the retention period with its source. Notes which events tenants can see in their own audit log.

**Red flags:**

- Audit emitted only from the calling app 'if needed'
- Audit written after the change in a separate best-effort call that can fail silently
- Application role can UPDATE or DELETE audit rows
- Audit events lack actor or tenant

### `observability` Observability

**Question:** When the package misbehaves in production, can an engineer see what happened for which tenant and request, without the package leaking personal data into telemetry?

- Which spans does the package create, and do they follow OpenTelemetry semantic conventions and propagate W3C trace context through BullMQ jobs and Temporal activities?
- Which metrics does it export (calls, errors by error type, latency histograms, queue depth, cache hit rate), and are labels bounded (tenant ID as a label only where cardinality is acceptable)?
- Are logs structured (JSON) with tenant ID, region, request ID and trace ID on every line, and is personal data redacted?
- What service level does the package promise its consumers (e.g. p99 latency, error rate), and is there an alert when it is breached?
- Can one tenant's activity be isolated in dashboards to answer a client's support question or an incident query?

**Good answer:** Lists the span names, metric names with labels and units, and log fields, and confirms trace propagation across async hops with a test. States the package-level objective (for example 'notify() p99 under 300 ms excluding provider time, errors under 0.5%') and the alert tied to it with a runbook link.

**Red flags:**

- console.log as the only telemetry
- Trace context lost when work moves to a queue or workflow
- Unbounded metric labels such as user ID or document ID
- Telemetry contains email addresses, names or document contents

### `resilience` Failure behaviour

**Question:** What does the package do when its own dependencies are slow, down or return duplicates, and can callers (including Temporal workflows) rely on it being safe to retry?

- Which calls are idempotent, what is the idempotency key, how long is it remembered, and where is it stored (tenant-scoped)?
- What timeouts does each outbound call have, and are they shorter than the caller's own timeout (HTTP request, Temporal activity start-to-close)?
- Which errors are retryable and which are not, and does the package retry internally or leave that to Temporal / BullMQ (and never both, to avoid retry storms)?
- Is the package safe to call from a Temporal activity (no hidden global state, deterministic error types) and never from workflow code where non-determinism would break replay?
- How does it behave under connection limits (PgBouncer pool size, Redis max clients) and does it release connections on error?
- If a non-critical dependency fails (for example the cache), does the package degrade gracefully rather than fail the whole call?

**Good answer:** A small table of dependencies with timeout, retry owner, idempotency behaviour and degraded mode. States clearly that retries live in one layer (usually Temporal or BullMQ) and the package exposes typed retryable / non-retryable errors that map to Temporal's non-retryable error types.

**Red flags:**

- No timeouts on outbound calls
- Internal retries plus caller retries with no coordination
- Mutating operations with no idempotency key
- Package code intended to run inside Temporal workflow code but uses time, random or I/O directly

### `change-safety` Change and release safety

**Question:** Because every app imports this package, how is a change released so that it cannot break consumers or all tenants at once?

- How are breaking changes detected before merge (API extractor / type-level diff, contract tests run against every consumer in the monorepo via Turborepo affected graph)?
- Is risky new behaviour released behind a feature flag that can be turned on per tenant and per region, and turned off without a deploy?
- Are database migrations owned by this package backwards-compatible with the previous app version (expand, migrate, contract) so a rollback does not fail?
- Who owns the package (CODEOWNERS), and which reviewers are required for changes to the public API?
- How are deprecated functions marked, how long are they kept, and what tool tells consumers they are still using them?
- Are module boundaries enforced so consumers cannot import internal files that are not part of the public API?

**Good answer:** Names the tools that guard the public API (type-level API report checked in CI, Turborepo boundaries, CODEOWNERS on the package), the flagging approach for behavioural changes, and the migration pattern. Gives the deprecation window and how removal is tracked to zero callers before deletion.

**Red flags:**

- Consumers import from deep internal paths
- Behaviour changes shipped to all tenants in one deploy with no flag or staged rollout
- Migrations that drop or rename columns in the same release that stops using them
- No named owner

### `testing` Testing

**Question:** Which tests prove the package's contract, its tenant isolation and its failure behaviour, and do they run automatically on every change that could affect it?

- Which unit tests cover the public API, and what coverage threshold is enforced in CI for this package?
- Are there integration tests against a real Postgres with forced RLS and PgBouncer in transaction mode (not mocks), including a test that tenant A cannot see tenant B's rows?
- Are there contract tests that consumers rely on, and do they run when either the package or a consumer changes?
- Are failure modes tested: dependency timeouts, duplicate calls with the same idempotency key, missing tenant context, region mismatch?
- Is a test double or in-memory fake provided to consumers, and is it itself tested against the real implementation so it does not drift?
- For a UI design-system package, are accessibility checks (WCAG 2.2 AA) automated for every component?

**Good answer:** Lists test layers with what each proves, the CI job that runs them, and the gates (for example coverage over 80% on public API, all isolation tests pass). Includes named negative tests for cross-tenant access, missing context and duplicate requests, and explains how the fake offered to consumers is kept honest.

**Red flags:**

- Tenant isolation tested only with mocked Prisma
- No negative tests (only happy paths)
- Tests not wired into CI for downstream consumers
- Fakes that consumers use but that are never checked against the real behaviour

