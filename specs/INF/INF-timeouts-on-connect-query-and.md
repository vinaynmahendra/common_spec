---
id: "INF-timeouts-on-connect-query-and"
title: "Database timeouts and retries"
parent: "INF-database-connection-handling"
order: 4
type: "feature"
template: "requirement"
status: "draft"
owner: null
indicative: false
summary: "Explicit timeouts on connect, pool acquire, statement and idle-in-transaction for every workload; whole-transaction retries with backoff only for transient, retryable errors"
links: []
rev: 4
syncHash: "9a8320c34e6d9d7c"
createdAt: "2026-10-28T02:44:44Z"
updatedAt: "2026-10-28T08:00:00Z"
updatedBy: null
---

# 14.7.3 Database timeouts and retries

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Explicit timeouts on connect, pool acquire, statement and idle-in-transaction for every workload; whole-transaction retries with backoff only for transient, retryable errors

<!-- section:statement -->
## Statement

Every database connection profile shall define explicit, non-zero limits for connection establishment, pool acquire wait, statement duration, interactive transaction duration and idle time inside a transaction, and if a transaction fails with an error classified as transient, then the data-access package shall retry the whole transaction at most 3 times with exponential backoff and jitter.

<!-- section:rationale -->
## Rationale and source

Without explicit limits, one slow query or one stuck transaction holds a pooled connection indefinitely; under transaction pooling, a transaction left open (for example by an unawaited promise) also blocks a PgBouncer server connection for everyone. Some defaults are unlimited: the `pg` driver's `connectionTimeoutMillis` defaults to 0 (no timeout) in Prisma v7 [R1]. Failovers ([[INF-database#resilience]]) produce short bursts of connection errors that a retry turns into a latency spike instead of a user-visible failure.

**Values (proposed)**

| Limit | `web` | `worker-jobs` / `worker-temporal-*` | Where set |
|---|---|---|---|
| Connect timeout | 5 s | 5 s | Driver (`connectionTimeoutMillis` / `connect_timeout`) |
| Pool acquire wait | 3 s | 10 s | Prisma v7 `pg` pool / v6 `pool_timeout`; PgBouncer `query_wait_timeout` 10 s as backstop |
| Statement | 15 s | 120 s | `ALTER ROLE nomo_app SET statement_timeout = '15s'` (role default survives PgBouncer) |
| Interactive transaction | `maxWait` 3 s, `timeout` 10 s | `timeout` 60 s | Prisma `$transaction` options in the tenant extension |
| Idle in transaction | 10 s | 30 s | `ALTER ROLE … SET idle_in_transaction_session_timeout` |

Migration and reporting values are in [[INF-separate-connection-settings-for]].

**Retryable (transient) errors**: connection failures (`ECONNRESET`, `ECONNREFUSED`, Prisma `P1001`, `P1017`), pool timeout (`P2024`) only for idempotent reads, Postgres `57P01 admin_shutdown`, `08006`, `40001 serialization_failure`, `40P01 deadlock_detected` (Prisma `P2034`). **Never retried**: constraint violations, `42501` insufficient privilege (RLS `WITH CHECK` failure), statement timeout `57014`, validation errors. Backoff: 100 ms, 400 ms, 1.6 s with ±50% jitter; total retry time under the request's own deadline.

Parent: [[INF-database-connection-handling]].

<!-- section:acceptance -->
## Acceptance criteria

- **Given** the `web` profile, **when** a query runs longer than 15 s, **then** Postgres cancels it with `57014`, the request returns a 503 problem type ([[APP-api-error-catalogue-problem]]) and it is **not** retried.
- **Given** a transaction that opens and then waits without sending a statement, **when** 10 s pass, **then** Postgres terminates the session and PgBouncer frees the server connection.
- **Given** a forced Postgres failover in staging, **when** requests are in flight, **then** affected transactions are retried and at least 99% of requests in the failover minute succeed within 10 s.
- **Negative**: **Given** an insert that violates RLS `WITH CHECK` (`42501`), **when** it fails, **then** no retry happens and a security event is emitted ([[OBS-security-events]]).
- **Negative**: **Given** a profile with any timeout missing or set to 0, **when** the container starts, **then** start-up validation fails.

<!-- section:verification -->
## Verification method

- **Test**: integration tests against real Postgres through PgBouncer (Testcontainers) for statement timeout, idle-in-transaction termination and retry classification.
- **Demonstration**: quarterly failover drill measures the success rate during the failover minute.
- **Inspection**: weekly grant / parameter check confirms role-level timeouts in every region.

<!-- section:priority -->
## Priority

Must. Phase 1.

<!-- section:notes -->
## Notes

**Open questions**

- [ ] Are 15 s (`web`) and 120 s (workers) right for the heaviest legitimate queries (secretariat queue filters, eBundle index building)? Long work should move to Temporal activities rather than raising the limit.
- [ ] Should writes that are not naturally idempotent carry an idempotency key so they can be retried safely after an ambiguous commit failure ([[APP-server-actions-and-mutation]])?

<!-- checks -->
## Template checks

<!-- check:necessary -->
### Necessary

Without explicit limits a single stuck transaction can hold a PgBouncer server connection indefinitely and the `pg` driver can wait forever to connect; without retries every failover becomes user-visible errors.

<!-- check:singular -->
### Singular

The statement combines two linked behaviours (limits and retries). They are kept together because retry budgets depend on the timeout values; if reviewers prefer, split the retry rule into its own unwanted-behaviour requirement.

<!-- check:feasible -->
### Feasible

Role-level `statement_timeout` and `idle_in_transaction_session_timeout` work through PgBouncer transaction pooling because they apply when the server connection is opened; Prisma exposes transaction `maxWait` / `timeout`; driver timeouts are configurable [R1].

<!-- check:verifiable -->
### Verifiable

Integration tests cover each limit and the retry classification with negative cases (no retry on `57014` and `42501`); the failover drill measures the user-visible success rate.

<!-- check:consistent -->
### Consistent

The worst case for a `web` request is PgBouncer wait (`query_wait_timeout` 10 s, [[INF-pgbouncer#config]]) plus statement time (15 s), which is still below the load balancer idle timeout (60 s), so the database path gives up first and the API can return a clean problem response. The app-side acquire wait (3 s) is shorter than PgBouncer's backstop, so the container normally fails first.

<!-- citations -->
## Citations

```json
[
  {
    "excerpt": "With driver adapters, pool configuration comes from the driver; for pg the v6 connection_limit maps to max (default 10) and the acquire timeout maps to connectionTimeoutMillis, which defaults to 0 (no timeout).",
    "id": "R1",
    "kind": "vendor",
    "title": "Prisma ORM v7: Connection pool",
    "url": "https://www.prisma.io/docs/orm/v7/prisma-client/setup-and-configuration/databases-connections/connection-pool",
    "vendor": "Prisma"
  }
]
```

<!-- end -->
