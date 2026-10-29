---
id: "INT-integration-framework"
title: "Integration framework"
parent: "INT"
order: 1
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "packages/integrations-core: connector interface with data manifests, per-tenant, per-unit and per-user connections, credential vault on the regional secrets manager, OAuth flows, data policy hook, inbound webhook receiver and inbox, outbound call wrapper, health probes, usage metering and sync jobs"
links: []
rev: 3
syncHash: "7e55926c7f305727"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 9.1 Integration framework

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> packages/integrations-core: connector interface with data manifests, per-tenant, per-unit and per-user connections, credential vault on the regional secrets manager, OAuth flows, data policy hook, inbound webhook receiver and inbox, outbound call wrapper, health probes, usage metering and sync jobs

<!-- section:purpose -->
## Purpose and scope

Shared mechanics for every provider integration, so each provider node ([[INT-common-integrations]] children, [[BIL-payment-gateway-integration]]) only writes its adapter and data mapping. It provides:
- a **connector** interface and registry, including each operation's **data manifest** (data kinds and tiers it sends);
- **connections**: a tenant's (or a unit's) configured instance of a connector, platform-managed, tenant-owned (BYO) or user-connected, per region;
- a **credential vault** on the regional secrets manager, including OAuth 2.0 authorisation-code and client-credentials flows with token refresh, named and per-user credentials (pattern borrowed from: named and external credentials in Salesforce [R4]);
- a **policy hook**: every outbound call is evaluated by [[INT-connector-data-policies]] before it leaves;
- an **inbound webhook receiver** with signature verification, tenant resolution and an idempotent inbox;
- an **outbound call wrapper** (timeouts, retry classification, idempotency keys, per-provider-per-tenant rate limiting, circuit breaker, audit and telemetry, usage metering);
- **health probes** and **sync jobs**: scheduled probes, pulls and reconciliations with stored cursors.

Administration of all of this (catalogue, connection lifecycle, unit enablement, defaults, health and usage views, rotation, revocation, admin API) is specified in [[INT-connections-admin]]; settings in [[PKG-settings-integrations]].

It does **not** contain provider-specific mapping, business rules, notification templates or our own public API (see [[INT-public-api-and-webhooks]]).

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use |
|---|---|
| [[PKG-notifications]] | Send email / SMS / WhatsApp via `MessagingProvider`; receive delivery receipts through the inbox |
| [[DOM-hearings]] workers | Create rooms, mint join tokens, receive `recording.ready` |
| [[DOM-documents]] / award flows | Create e-sign envelopes, receive `envelope.completed` |
| [[DOM-neutrals]], [[DOM-invoices-and-vendor-bills]] | KYC and sanctions checks before payouts |
| [[BIL-payment-gateway-integration]] | Payment intents, refunds, settlement sync |
| [[INT-accounting-sync]] | Post journal data to Odoo, reconcile |
| [[WF-automation-rules]], [[WF-ai-steps-and-agents]] | Connector actions inside automations and AI steps, evaluated against data policies |
| [[INT-connections-admin]] (admin API and consoles) | Create, configure, test, enable per unit, rotate, disable and revoke connections; health and usage |
| [[PKG-personalisation]] | Per-user connected accounts (calendar) |

<!-- section:api -->
## Public API

```ts
// packages/integrations-core/src/index.ts  (server-only)
export type ProviderCategory = 'video'|'esign'|'kyc'|'messaging'|'accounting'|'payments'|'calendar';
export type OwnershipModel = 'platform_managed'|'tenant_byo'|'user_connected';
export type DataKind = 'contact_pii'|'identity_document'|'case_metadata'|'case_parties_other_side'
  |'document_content'|'recording_media'|'financial'|'system_reference';
export type Tier = 'public'|'tenant_internal'|'case_participants'|'tribunal_only';

export interface OperationManifest { name: string; mutating: boolean; sends: Array<{ kind: DataKind; tier: Tier }> }

export interface ConnectorDefinition<Cfg, Client> {
  key: string;                         // 'zoom', 'aadhaar-esign-esp-x', 'odoo', ...
  category: ProviderCategory;
  regions: Array<'in'|'sg'|'us'>;      // regions with a compliant endpoint/account
  ownershipModels: OwnershipModel[];
  configSchema: z.ZodType<Cfg>;        // non-secret config, validated on save
  secretSchema: z.ZodType<unknown>;    // shape of the secret stored in the vault
  auth: { kind: 'api_key'|'oauth_client_credentials'|'oauth_authorization_code'|'mtls'|'basic'; scopes?: string[] };
  operations: OperationManifest[];     // checked by manifest conformance tests
  probe(client: Client): Promise<ProbeResult>;   // read-only health and capability check
  createClient(ctx: ConnectionContext<Cfg>): Client;
  webhook?: {
    verify(raw: Buffer, headers: Headers, secret: unknown): VerifiedProviderEvent; // throws WebhookSignatureError
    eventId(e: VerifiedProviderEvent): string;     // provider's unique event id
  };
  meters?: Array<'sms_segments'|'esign_envelopes'|'kyc_checks'|'video_minutes'>;
}

export function registerConnector(def: ConnectorDefinition<any, any>): void;

export async function getConnection(connectionId: string): Promise<Connection>; // tenant from context
export async function withConnection<C, R>(
  category: ProviderCategory, fn: (client: C, conn: Connection) => Promise<R>,
  opts?: { connectionId?: string; unitId?: string; userId?: string /* per-user credential */ }
): Promise<R>;   // resolves: explicit id → case-type pin → unit default → tenant default (integration.default_connection.<category>)

export async function callProvider<R>(conn: Connection, op: {
  name: string;                         // must match an OperationManifest
  idempotencyKey?: string;              // required for mutating ops
  timeoutMs: number;
  payloadTags?: Array<{ kind: DataKind; tier: Tier }>; // from tagged domain fields; evaluated with the manifest
  classify?: (err: unknown) => 'retryable'|'non_retryable'|'rate_limited';
}, fn: (signal: AbortSignal) => Promise<R>): Promise<R>;   // throws ConnectorPolicyViolationError before calling out

// Inbound
export function webhookRoute(): (req: Request, ctx: { params: { provider: string; connectionId: string } }) => Promise<Response>;
export function onProviderEvent(provider: string, type: string,
  handler: (e: InboxEvent, conn: Connection) => Promise<void>): void;  // run by a BullMQ worker

// OAuth
export async function beginOAuth(connectorKey: string, p: { connectionId: string; redirectAfter: string; perUser?: boolean }): Promise<{ authorizeUrl: string }>;
export async function completeOAuth(state: string, code: string): Promise<Connection>;

// Administration primitives (called only by the admin API in INT-connections-admin)
export async function createConnection(tx: TenantTx, input: CreateConnectionInput): Promise<Connection>;
export async function writeCredential(tx: TenantTx, connectionId: string, secret: unknown, opts: { pending: boolean }): Promise<void>;
export async function probeConnection(connectionId: string): Promise<ProbeResult>;      // enqueues integration-probe:{region}
export async function setConnectionState(tx: TenantTx, connectionId: string, to: ConnectionState, reason: string): Promise<void>;
export async function revokeConnection(tx: TenantTx, connectionId: string, reason: string): Promise<{ workflowId: string }>;

// Sync jobs
export function defineSync(key: string, opts: { schedule: string; run: (conn: Connection, cursor: string|null) => Promise<{ nextCursor: string|null }> }): void;

// Events emitted on the outbox
// integration.connection.created | .updated | .state_changed | .credential_rotated | .health_changed | .usage_threshold_reached
```

**Tables owned** (tenant-owned, forced RLS): `integration_connection` (fields in [[INT-connections-admin#mapping]]), `integration_connection_unit`, `integration_user_credential`, `provider_event_inbox(id, tenant_id, connection_id, provider, provider_event_id, event_type, received_at, raw_body_ciphertext bytea, status 'received'|'processed'|'failed'|'ignored', attempts, UNIQUE(tenant_id, connection_id, provider_event_id))`, `integration_sync_cursor(tenant_id, connection_id, sync_key, cursor, last_run_at)`, `integration_call_log` (monthly partitions, 30-day retention: op name, status, duration, provider request ID, idempotency key, policy decision; no bodies), `integration_usage_daily(tenant_id, connection_id, meter, day, quantity)`. Platform-level: `connector_catalogue_entry`, `connector_availability`, `platform_integration_connection`.

<!-- section:usage -->
## Usage examples

```ts
// Temporal activity: create an e-sign envelope idempotently
export async function createEnvelope(input: { documentVersionId: string; signers: SignerRef[] }) {
  return withConnection<ESignClient, EnvelopeRef>('esign', (client, conn) =>
    callProvider(conn, {
      name: 'esign.createEnvelope',
      idempotencyKey: `env:${input.documentVersionId}`,
      timeoutMs: 15_000,
    }, (signal) => client.createEnvelope(input, { signal })));
}
// Errors: IntegrationNotConfiguredError (non-retryable → human task),
//         ProviderRateLimitedError (Temporal retries with backoff),
//         ProviderNonRetryableError (fail activity, no retry)
```

```ts
// app/api/integrations/webhooks/[provider]/[connectionId]/route.ts
export const POST = webhookRoute();   // verify → resolve tenant → insert inbox → enqueue → 200
```

<!-- section:tenant -->
## Tenant context

- Outbound: `withConnection` reads the tenant (and unit and user where relevant) from the async request / Temporal interceptor context ([[MT-prisma-client-extension-wraps]], [[WF-separation-of-concerns-temporal#guardrails]]); a missing context throws `TenantContextMissingError` before any provider call. Passing a `connectionId` from another tenant returns not-found (RLS hides it). A unit-scoped call can use only connections enabled for that unit.
- Inbound: the URL carries `connectionId`. The receiver looks it up through a narrow resolver function (the only pre-tenant lookup, returning `tenant_id`, `region`, `connector_key`, `status` and the secret reference), checks the region equals the running region (else 421 Misdirected Request and an alert), verifies the signature with that connection's secret, then opens a tenant-scoped transaction to insert into the inbox. The handler re-checks that every referenced entity (case, envelope, payment) belongs to that tenant.
- Per-user credentials are resolved only for the user in context; a job acting for user A can never load user B's credential.
- Redis keys (rate limits, circuit state) are `int:{region}:{tenantId}:{connectorKey}:...`; BullMQ jobs carry `tenantId` and the worker sets context per job.
- Isolation rules follow [[MT-isolation-strategy]].

<!-- section:config -->
## Configuration

All tunable behaviour is read through [[PKG-settings]] using the keys in [[PKG-settings-integrations]] (connection defaults per category and scope, ownership models allowed, rotation days, health intervals and thresholds, usage caps, data policy switches). Values that are engineering constants stay in code:

| Constant | Value | Changed by |
|---|---|---|
| Connector availability per region | connector definition + `integration.connector.<key>.availability` | Platform engineering / platform admin |
| Rate limit per provider per tenant | provider's documented limit ÷ expected active tenants, min 1 req/s | Platform engineering (connector config) |
| Webhook timestamp tolerance | 300 s | Security review |
| Outbound timeout | per operation, 5–30 s | Adapter owner |
| Inbox raw-body retention | 90 days (8 years for payments, KYC and e-sign evidence events) | Privacy owner via [[PKG-retention-and-deletion-schedule]] |

<!-- section:adapters -->
## Providers and extension points

Credentials are stored in the regional secrets manager at `/{env}/{region}/integrations/{connectorKey}/platform` (platform-owned accounts) or `/{env}/{region}/tenants/{tenantId}/integrations/{connectionId}` (tenant-owned). Only `secret_ref` is stored in Postgres. OAuth: authorisation-code with PKCE and `state` bound to the user session and tenant for tenant-owned accounts (for example calendar); client-credentials or signed-JWT client authentication for platform accounts; refresh tokens rotated and stored in the vault; access tokens cached in memory only [R1]. Rotation: platform credentials every 90 days or on staff change (runbook), tenant credentials when the tenant reconnects; rotation emits `integration.connection.credential_rotated`.

Adding a connector: implement `ConnectorDefinition`, list its regions, add contract-test fixtures, complete the vendor assessment ([[SEC-vendor-sub-processor-management]]) and add a row to [[INT-third-party-component]] if it renders UI.

<!-- section:errors -->
## Error model

| Error | Retryable | Caller action |
|---|---|---|
| `TenantContextMissingError` | No | Bug; fail fast |
| `IntegrationNotConfiguredError` | No | Create a human task for the tenant admin; show a clear message |
| `IntegrationDisabledError` (suspended connection, region mismatch) | No | Same as above |
| `ProviderRateLimitedError` (429, with retry-after) | Yes, after delay | Let Temporal / BullMQ retry; do not retry inside the wrapper |
| `ProviderUnavailableError` (5xx, timeout, circuit open) | Yes | Retry with backoff; degrade per provider node |
| `ProviderNonRetryableError` (4xx validation) | No | Fail; record in call log; surface to operator |
| `WebhookSignatureError` | No | 401; security event; no inbox row |

Rule: the wrapper never retries; retries belong to Temporal or BullMQ, so there is exactly one retry layer.

<!-- section:nfr -->
## Performance and limits

- Inbound receiver: p99 < 300 ms to acknowledge (verify + insert + enqueue), payload limit 1 MB (larger provider payloads are fetched by reference), 50 req/s per connection before 429.
- Outbound wrapper overhead: < 5 ms p99 excluding the provider call.
- Circuit breaker: opens after 50% failures over 20 calls in 60 s per connector per region; half-open probe every 30 s.
- Proposed targets; to be validated in [[TST-performance-and-load-testing]].

<!-- section:versioning -->
## Versioning and compatibility

SemVer for `packages/integrations-core`; adapters depend on a major version. Breaking changes to `ConnectorDefinition` require all adapters in the monorepo to compile in the same PR (Turborepo affected graph). Provider API version changes are handled inside the adapter and tracked in the provider node's testing section.

<!-- section:testing -->
## Test contract

- Unit tests for the wrapper's classification, idempotency key enforcement and rate limiter.
- Integration tests against real Postgres with forced RLS through PgBouncer: inbound event for connection of tenant A cannot be read or processed under tenant B; forged `connectionId` returns 404; unsigned event yields 401 and no row; duplicate provider event ID yields one row.
- Region test: a connection created for region `sg` called in region `in` raises `IntegrationDisabledError`.
- A fake connector (`fake-provider`) with recorded fixtures is provided to consumers and checked against the same contract tests as real adapters.

<!-- section:questions -->
## Open questions

- [ ] Is a generic integration-hub product (open source) worth using for OAuth token management, or is the in-house vault enough (proposed: in-house)?
- [ ] Inbox raw-body retention for non-evidential events (proposed 90 days).
- [ ] Which categories allow `tenant_byo` at launch: payments and calendar (as before), plus messaging and e-sign for institutions (proposed in [[PKG-settings-integrations#defaults]])?
- [ ] Egress control: per-connector host allow-lists at the network layer ([[INF-networking]]) in addition to code checks?
- [ ] Should payload data kind tags come from Prisma model field annotations (generated) or from explicit tags at each call site? Proposed: generated from a field classification registry shared with [[SEC-data-classification]].

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

Outbound calls take tenant only from context and resolve connections through RLS-protected tables; inbound events are resolved to exactly one tenant by `connectionId` through one narrow, reviewed resolver function before any tenant-scoped write, with region check and per-connection signing secret. Redis keys and BullMQ jobs are tenant- and region-prefixed through one helper. Handlers re-verify that referenced entities belong to the resolved tenant. The resolver is the only pre-tenant path and is covered by dedicated isolation tests.

<!-- check:security -->
### Security of the API surface

Inputs are Zod-validated (`configSchema`, `secretSchema`). Credentials live only in the regional secrets manager, referenced by path; the web role can write but not read them; OAuth uses PKCE and state binding, short-lived cached access tokens and rotated refresh tokens [R1]. Every outbound call passes the data policy evaluator before leaving. Webhooks are verified on the raw body with a 300-second timestamp tolerance and event-ID replay protection [R2]; our own outbound webhooks follow the Standard Webhooks scheme [R3]. Provider-supplied download URLs are fetched only from hosts listed in the connector definition (SSRF control), and downloaded files go through malware scanning ([[PKG-encryption-at-rest-signed-urls]]). The package is server-only and vendor SDKs are restricted to integration packages by a boundary rule.

<!-- check:audit -->
### Audit events

Connection create, update, state change, unit enablement, credential write (never the value) and rotation are audited with actor, principal and tenant (`admin.integration.*`). Each outbound mutating call writes an audit event with operation name, provider request ID, idempotency key and policy decision (no bodies); evidential responses are stored as documents by the calling domain. Inbox rows keep the verified raw body (encrypted) for the retention period.

<!-- check:observability -->
### Observability

Metrics per connector, region and operation: call count by outcome class, latency histogram, 429 count, circuit state, inbox received versus processed, signature failures, sync lag. Tenant ID is a label only on low-cardinality counters; detailed per-tenant views come from logs and traces. W3C trace context flows from the user action through Temporal or BullMQ to the provider call and from the inbox back to the workflow signal, with the provider reference stored on the span.

<!-- check:resilience -->
### Failure behaviour

Mutating calls require an idempotency key (the wrapper throws if missing). Timeouts are per operation and shorter than the activity's start-to-close timeout. The wrapper classifies errors but never retries; Temporal or BullMQ owns retries, avoiding retry storms. Circuit breaker per connector per region; non-critical calls (health checks, lookups) degrade instead of failing the user action. Safe to call from activities; never from workflow code.

<!-- check:change-safety -->
### Change and release safety

`ConnectorDefinition` changes are SemVer-major and must compile across all adapters in one PR; new manifest kinds require a policy evaluator update in the same release; changes to default-connection resolution are covered by a pinned-connection regression test so running cases cannot switch providers on deploy.

<!-- check:testing -->
### Testing

See Test contract: RLS-backed isolation tests through PgBouncer, signature and duplicate tests, region mismatch, and a fake connector tested against the same contract suite as real adapters.

<!-- citations -->
## Citations

```json
[
  {
    "body": "IETF",
    "excerpt": "Recommends sender-constrained or audience-restricted, short-lived access tokens and strong client authentication such as private_key_jwt.",
    "id": "R1",
    "ident": "RFC 9700",
    "kind": "standard",
    "title": "Best Current Practice for OAuth 2.0 Security",
    "url": "https://www.rfc-editor.org/rfc/rfc9700.html"
  },
  {
    "body": "OWASP",
    "excerpt": "Guidance on signing webhook payloads, timestamp checks against replay, and SSRF protection when delivering to user-supplied URLs.",
    "id": "R2",
    "kind": "standard",
    "title": "OWASP Webhook Security Cheat Sheet",
    "url": "https://cheatsheetseries.owasp.org/cheatsheets/Webhook_Security_Cheat_Sheet.html"
  },
  {
    "excerpt": "Defines webhook-id, webhook-timestamp and webhook-signature headers with an HMAC-SHA256 signature over id.timestamp.payload, and secret rotation with multiple signatures.",
    "id": "R3",
    "kind": "web",
    "publisher": "Standard Webhooks (open specification)",
    "retrieved": "2026-10-28",
    "title": "Standard Webhooks specification",
    "url": "https://github.com/standard-webhooks/standard-webhooks"
  },
  {
    "excerpt": "A named credential defines the callout endpoint; an external credential defines how the caller authenticates, and principals map to user permissions.",
    "id": "R4",
    "kind": "vendor",
    "publisher": "Salesforce",
    "retrieved": "2026-10-28",
    "title": "Get Started with Named Credentials",
    "url": "https://developer.salesforce.com/docs/platform/named-credentials/guide/get-started.html"
  }
]
```

<!-- end -->
