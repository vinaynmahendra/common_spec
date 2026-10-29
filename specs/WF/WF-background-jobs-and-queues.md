---
id: "WF-background-jobs-and-queues"
title: "Background jobs and queues"
parent: "WF"
order: 2
type: "capability"
template: "package"
status: "draft"
owner: null
indicative: false
summary: "**BullMQ on Redis** (retries, dead-letter queues, scheduling, rate limiting)"
links: []
rev: 3
syncHash: "9fd26f19400be810"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 7.2 Background jobs and queues

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> **BullMQ on Redis** (retries, dead-letter queues, scheduling, rate limiting)

<!-- section:purpose -->
## Purpose and scope

`packages/jobs` is the only way apps and workers use BullMQ. It defines the queue catalogue, a tenant-aware `enqueue` with idempotency, a worker wrapper that restores tenant context and trace context, standard retry and backoff, dead-letter handling, per-tenant fairness and rate limits, and metrics. BullMQ runs on the regional Redis ([[INF-redis]]) chosen in [[ADR-queue-technology]].

**Does not do**: durable multi-step processes or legal timers (Temporal, see [[WF-workflow-engine]]), entity status changes ([[WF-entity-state-machines]]), or caching ([[PKG-caching]]), even though caching shares the Redis deployment.

<!-- section:consumers -->
## Consumers and use cases

| Consumer | Use |
|---|---|
| [[PKG-notifications]] | `notifications.send`: deliver one message on one channel to one recipient |
| [[PKG-storage]] / [[PKG-encryption-at-rest-signed-urls]] | `files.scan` malware scan of each uploaded object; `files.thumbnail` |
| [[PKG-search]] | `search.index` / `search.delete` for one document or case |
| [[APP-webhooks-outbound]] | `webhooks.deliver`: one delivery attempt to one tenant endpoint |
| Outbox relay ([[WF-workflow-engine]]) | `outbox.relay` repeatable job per region: publishes outbox rows to Temporal starts / signals, webhooks and search |
| [[INT-accounting-sync]] | `accounting.sync`: push one invoice, payment or bill to the accounting system |
| Temporal activities | Enqueue single side effects with `jobId = {workflowId}:{activityId}` |

<!-- section:api -->
## Public API

```ts
// packages/jobs/src/index.ts
export type QueueName =
  | 'notifications.send' | 'files.scan' | 'files.thumbnail' | 'search.index' | 'search.delete'
  | 'webhooks.deliver' | 'outbox.relay' | 'accounting.sync';

export interface QueueDef<P extends z.ZodTypeAny> {
  name: QueueName;
  payload: P;                                   // zod schema, validated on enqueue and on process
  attempts: number;                             // default 8
  backoff: { type: 'exponential' | 'fixed'; delayMs: number };
  concurrency: number;                          // per worker process
  limiter?: { max: number; durationMs: number };          // global per region
  tenantFairness?: { maxActivePerTenant: number; tokensPerSecond?: number };
  timeoutMs: number;                            // hard limit for the handler
  piiFree: true;                                // compile-time marker: payload must hold IDs only
}

export function defineQueue<P extends z.ZodTypeAny>(def: QueueDef<P>): QueueDef<P>;

export interface EnqueueOptions {
  idempotencyKey: string;        // becomes the BullMQ jobId; required
  delayMs?: number;              // not for legal deadlines (use Temporal)
  priority?: 1 | 2 | 3;          // 1 = interactive (e.g. OTP), 3 = bulk
}
export function enqueue<P extends z.ZodTypeAny>(
  ctx: TenantContext, queue: QueueDef<P>, payload: z.infer<P>, opts: EnqueueOptions,
): Promise<{ jobId: string; deduplicated: boolean }>;

export function enqueueBulk<P extends z.ZodTypeAny>(
  ctx: TenantContext, queue: QueueDef<P>, items: Array<{ payload: z.infer<P>; idempotencyKey: string }>,
): Promise<{ accepted: number; deduplicated: number }>;

export interface JobContext<T> {
  tenantId: string; region: Region; jobId: string; attempt: number;
  payload: T;
  withTenantTx<R>(fn: (tx: TenantPrisma) => Promise<R>): Promise<R>;   // Prisma tx with app.tenant_id set
  log: Logger; span: Span;
}
export function createWorker<P extends z.ZodTypeAny>(
  queue: QueueDef<P>, handler: (job: JobContext<z.infer<P>>) => Promise<void>,
): JobsWorker;

export class NonRetryableJobError extends Error { constructor(code: string, message: string) }
export class TenantThrottled extends Error {}          // internal: job re-delayed, attempt not consumed

export function listDeadLetters(ctx: PlatformOpsContext, queue: QueueName, filter?: { tenantId?: string }): Promise<DeadLetter[]>;
export function replayDeadLetter(ctx: PlatformOpsContext, queue: QueueName, jobId: string, reason: string): Promise<void>;
```

**Job envelope** stored in Redis (the only shape a worker accepts):

```json
{ "v": 1, "tenantId": "…", "region": "in", "idempotencyKey": "…", "traceparent": "00-…",
  "enqueuedBy": { "kind": "user|system|workflow", "id": "…" }, "enqueuedAt": "2026-10-28T10:00:00Z",
  "payload": { "notificationId": "…" } }
```

Everything not listed is internal.

<!-- section:usage -->
## Usage examples

```ts
// Enqueue a malware scan after upload completes (inside the documents service)
await enqueue(ctx, filesScan, { documentVersionId }, { idempotencyKey: `scan:${documentVersionId}` });

// Worker
createWorker(filesScan, async (job) => {
  const verdict = await scanner.scan(job.payload.documentVersionId);   // provider call with its own timeout
  await job.withTenantTx(tx => documents.recordScanVerdict(tx, job.payload.documentVersionId, verdict));
});

// From a Temporal activity: enqueue once even if the activity retries
export async function sendOnChannel(input: SendInput) {
  const { workflowId, activityId } = Context.current().info;
  return enqueue(ctxFrom(input), notificationsSend, { notificationId: input.notificationId },
    { idempotencyKey: `${workflowId}:${activityId}` });
}

// Fail fast on a permanent error
if (!recipient.email) throw new NonRetryableJobError('NO_CONTACT_POINT', 'Recipient has no email');
```

<!-- section:tenant -->
## Tenant context

- `enqueue` takes a `TenantContext` argument (from the request, the Temporal activity input or a parent job); there is no ambient default. A missing or platform context throws `MissingTenantContext` before anything reaches Redis.
- The envelope carries `tenantId` and `region`. The worker wrapper rejects (non-retryable, alerted) any job whose `region` is not the worker's region, and opens every database transaction through `withTenantTx`, which uses the Prisma extension from [[MT-prisma-client-extension-wraps]].
- The payload schema forbids a `tenantId` field inside `payload`, so there is a single source of truth.
- Platform jobs without a tenant (for example `outbox.relay` per region) are defined with `scope: 'platform'`, may only be enqueued with a `PlatformOpsContext`, and fan out to per-tenant jobs for any tenant work.
- Redis keys use the prefix `bull:{region}`; tenant IDs are not part of key names (job IDs include idempotency keys, which are built from IDs, not personal data).

<!-- section:config -->
## Configuration

| Setting | Default | Where | Who changes |
|---|---|---|---|
| Queue definitions (attempts, backoff, concurrency, limiter) | In code per queue | `packages/jobs/src/queues/*.ts` | Platform engineering via PR |
| Redis connection per region | Regional secret | Secrets manager ([[INF-secrets-and-keys]]) | DevOps |
| Per-tenant fairness caps | `maxActivePerTenant` per queue (proposed 20 for `notifications.send`, 5 for `files.scan`) | Code default, tenant override in [[PKG-settings]] for large tenants | Platform ops |
| Completed job retention | `removeOnComplete: { age: 3600, count: 5000 }` | Code | Platform engineering |
| Failed job retention before dead-letter | `removeOnFail: { age: 7 days }` | Code | Platform engineering |
| Worker replicas per queue | Per region | IaC ([[INF-orchestration]]) | DevOps |

<!-- section:adapters -->
## Providers and extension points

- **Queue backend**: BullMQ only. The package hides BullMQ types so that a move (for example to BullMQ Pro groups for fairness) does not change consumers.
- **Fairness strategy**: interface `FairnessStrategy { tryAcquire(tenantId, queue): Promise<boolean>; release(...) }`. Default implementation is a Redis counter semaphore per tenant and queue; when `tryAcquire` fails the wrapper moves the job back to delayed (BullMQ `DelayedError` pattern) with jitter, so the attempt is not counted.
- **Dead-letter sink**: on final failure the wrapper copies the job into `{queue}.dead` with error code, stack hash and attempts, and emits an alert metric.

<!-- section:errors -->
## Error model

| Error | Retryable | Caller action |
|---|---|---|
| `MissingTenantContext` | No | Programming error; fix the caller |
| `PayloadValidationError` | No | Fix the caller; dead-lettered immediately on the worker side |
| `RegionMismatch` | No | Routing bug; alert |
| `NonRetryableJobError(code)` | No | Handler decided; dead-lettered with code |
| `TenantThrottled` | Re-delayed | None; transparent |
| Any other error | Yes, with backoff [R1] | Retried until `attempts`, then dead-lettered |
| `EnqueueUnavailable` (Redis down) | Caller decides | In a request: return 503 with retry; in a Temporal activity: let Temporal retry |

<!-- section:nfr -->
## Performance and limits

Proposed targets per region:

| Measure | Target |
|---|---|
| `enqueue` latency p99 | under 20 ms |
| Wait time p95, `notifications.send` priority 1 | under 5 s; priority 3 under 5 min |
| Wait time p95, `files.scan` | under 60 s |
| Throughput | 200 jobs/s sustained per region across queues at launch |
| Payload size | 16 KB maximum (IDs only); larger inputs go to Postgres or object storage |
| Handler timeout | Per queue, maximum 5 minutes; anything longer belongs in Temporal |

<!-- section:versioning -->
## Versioning and compatibility

Semver within the monorepo; queue payload schemas are versioned by the envelope `v` and by additive payload changes only. A breaking payload change uses a new queue name (for example `search.index.v2`) and the old worker is kept until the old queue drains. Workers are deployed before producers for additive changes.

<!-- section:testing -->
## Test contract

- Unit tests for envelope building, schema validation and error classification.
- Integration tests against real Redis and Postgres (RLS, through PgBouncer): idempotent enqueue (same key twice gives one job, using BullMQ job IDs and deduplication [R2]), tenant context restored in the handler, region mismatch rejected, retries then dead-letter, throttling does not consume attempts.
- A fake in-memory queue for consumer unit tests, itself tested against the real implementation with the same contract suite.

<!-- section:questions -->
## Open questions

- [ ] Buy BullMQ Pro for group-based per-tenant fairness and rate limiting, or keep our Redis semaphore? Owner: platform engineering.
- [ ] Separate Redis instances for queues and cache per region (recommended to avoid eviction of queue keys), or one cluster with `noeviction`? Owner: DevOps with [[INF-redis]].
- [ ] Who may replay dead letters in production, and does replay of a tenant's job need tenant approval?

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation

`enqueue` requires an explicit `TenantContext`; the worker restores it from the envelope and every database call goes through `withTenantTx`, which sets `app.tenant_id` per transaction (safe under PgBouncer). The tenant ID is never read from the payload. Platform-scope jobs need a `PlatformOpsContext` and fan out to tenant jobs. Per-tenant fairness caps stop one tenant's bulk import from starving others' notifications.

<!-- check:security -->
### Security of the API surface

Payloads hold IDs only (enforced by schema review and a 16 KB limit), so Redis never holds document content or contact details. Redis is reached over TLS with per-region credentials from the secrets manager; workers run with the `nomo_worker` database role. Dead-letter replay is a platform-ops action, audited.

<!-- check:residency -->
### Region awareness

One Redis and one set of workers per region; the envelope carries the region and workers reject other regions' jobs. There is no cross-region queue.

<!-- check:audit -->
### Audit events

Jobs are not evidence. Handlers whose effect is legally significant (sending a notice message) record the outcome in Postgres (for example `notice_delivery_attempts`) and the audit log. Replays of dead letters are audited with actor and reason.

<!-- check:observability -->
### Observability

Metrics per queue and region: waiting, active, delayed, failed, dead-lettered counts; wait-time and processing-time histograms; throttle count per tenant (tenant as a label only on the throttle metric). W3C trace context is carried in the envelope so a job span joins the trace of the request or workflow that enqueued it. Alerts: dead letters above zero for `notifications.send` in 15 minutes; wait time above target for 10 minutes.

<!-- check:resilience -->
### Failure behaviour

Idempotency key = BullMQ job ID, so duplicate enqueues are dropped [R2]. Retries with exponential backoff are done by BullMQ only [R1]; handlers do not retry internally, and Temporal activities that enqueue rely on the job ID rather than re-enqueue loops. If Redis is unavailable, requests fail with 503 and Temporal activities retry; no fallback to another region.

<!-- check:change-safety -->
### Change and release safety

Payload changes are additive; breaking changes get a new queue name. Contract tests run for every consumer through the Turborepo affected graph. CODEOWNERS: platform engineering.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "BullMQ retries failed jobs up to the configured number of attempts with fixed or exponential backoff.",
    "id": "R1",
    "kind": "vendor",
    "title": "BullMQ docs: Retrying failing jobs",
    "url": "https://docs.bullmq.io/guide/retrying-failing-jobs",
    "vendor": "Taskforce.sh (BullMQ)"
  },
  {
    "excerpt": "BullMQ can ignore a job added with the same deduplication ID, and job IDs can be set by the caller.",
    "id": "R2",
    "kind": "vendor",
    "title": "BullMQ docs: Deduplication",
    "url": "https://docs.bullmq.io/guide/jobs/deduplication",
    "vendor": "Taskforce.sh (BullMQ)"
  }
]
```

<!-- end -->
