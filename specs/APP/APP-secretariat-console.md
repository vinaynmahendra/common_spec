---
id: "APP-secretariat-console"
title: "Secretariat console"
parent: "APP-route-groups-per-persona"
order: 3
type: "requirement"
template: "frontend"
status: "draft"
owner: null
indicative: false
summary: "Frontend architecture for the (secretariat) route group: high-volume case queues, bulk actions, scheduling, deadline tracking"
links: []
rev: 2
syncHash: "05d115050557ed92"
createdAt: "2026-10-28T04:25:50Z"
updatedAt: "2026-10-28T05:04:12Z"
updatedBy: null
---

# 2.1.2.3 Secretariat console

<!-- Generated layout: edit text between the markers; keep the markers and the front matter. -->

> Frontend architecture for the (secretariat) route group: high-volume case queues, bulk actions, scheduling, deadline tracking

<!-- section:scope -->
## Scope, audiences and surfaces

Frontend architecture of the `(secretariat)` route group, prefix `/secretariat`. Personas: case managers, tribunal secretaries and registry staff of the tenant institution. They work full days on managed Windows desktops (often with JAWS or NVDA), handle hundreds to thousands of cases (SEBI ODR institution tenants can receive large batches through the aggregator API, [[INT-aggregator-intake-api]]), and depend on keyboard speed.

Covers: case queues with saved views, case management pages, bulk actions, hearing scheduling, deadline tracking, human-task inbox, service of notices, intake review of filings from the public entry and aggregators.

Out of scope: tenant configuration ([[APP-tenant-admin-console]]), reports ([[RPT-platform-stats]]), the hearing room ([[APP-hearing-room-in-browser]]).

<!-- section:routing -->
## Routes, layouts and boundaries

```text
app/(secretariat)/secretariat/
  layout.tsx                          # shell; requirePersona('secretariat')
  page.tsx                            # my tasks + deadline radar
  queues/page.tsx                     # list of queues and saved views
  queues/[queueId]/page.tsx           # data table; filters, sort, cursor in URL
  intake/page.tsx                     # new filings and aggregator batches awaiting review
  intake/batches/[batchId]/page.tsx
  cases/[caseRef]/
    layout.tsx  error.tsx  not-found.tsx
    page.tsx                          # overview, parties, tribunal, status actions
    documents/  service/  hearings/  invoices/  tasks/  audit/
    @drawer/(.)parties/[partyId]/page.tsx    # side drawer
  hearings/schedule/page.tsx          # scheduler across tribunals and rooms
  deadlines/page.tsx                  # deadlines due in 7 days, breached, paused
  operations/[operationId]/page.tsx   # progress of bulk operations
```
`queues/[queueId]` carries all view state in the URL (`?stage=awaiting-response&sort=-nextDeadline&cursor=…`) so views can be shared between colleagues and survive reloads.

<!-- section:rendering -->
## Rendering and caching strategy

Dynamic, streamed; `private, no-store`. Queue pages server-render the first page of 50 rows in HTML; subsequent pages and filter changes go through tRPC with TanStack Query (`keepPreviousData`). Queue counts per saved view are computed on the server and may be cached for 30 seconds with `'use cache: remote'` keyed `(tenantId, userId, viewId)` and tagged `tenant:{tenantId}:queue-counts`. That user-specific cache is acceptable because the key includes the user; invalidated by case status changes.

<!-- section:data -->
## Data fetching and mutations

| Operation | Kind | Notes |
|---|---|---|
| `secretariat.queue.page` | tRPC query | cursor pagination, 50 rows, allow-listed filters mapped to indexed columns ([[PKG-data-table]]) |
| `secretariat.queue.counts` | tRPC query | cached 30 s as above |
| `secretariat.case.changeStatus` | tRPC mutation | validated against [[WF-entity-state-machines]]; reason required; audited |
| `secretariat.bulk.start` | tRPC mutation | Idempotency-Key header; selection sent as explicit IDs (max 500) or as a saved-view filter snapshot (max 10,000); starts workflow `{tenantId}-bulk-action-{operationId}`; returns `operationId` |
| `secretariat.bulk.status` | tRPC query, polled every 3 s | per-item results; failures downloadable as CSV |
| `scheduleHearing` | Server Action | uses [[PKG-date-and-time-picker-with]]; conflict check against no-overlap constraints ([[DOM-hearings-schema]]) |
| `secretariat.tasks.*` | tRPC | claim, complete, reassign human tasks ([[WF-human-tasks]]) |
| `serveNotice` | Server Action | starts service workflow ([[DOM-service-of-notices-and-proof]]) |
| `secretariat.intake.acceptBatch` | tRPC mutation | aggregator batch review |

<!-- section:state -->
## Client state and URL state

URL: queue, filters, sort, cursor, selected tab. TanStack Query: queue pages, counts, task inbox (refetch on window focus and every 60 s). Selection across pages is held in component state and cleared on filter change, with an announcement. Column choices per user are stored on the server as user settings ([[PKG-settings]]).

<!-- section:forms -->
## Forms, validation and uploads

Status changes and bulk actions use small dialog forms with a required reason (free text, 500 characters) and confirmation stating how many cases are affected. Scheduling form validates participant availability on the server and shows conflicts inline.

<!-- section:errors -->
## Error, loading and empty handling

| Situation | Handling |
|---|---|
| Illegal status transition | `INVALID_STATE_TRANSITION` problem; dialog explains the current state and allowed next states |
| Bulk operation partly fails | Operation page lists failed items with reason codes; retry for failed only |
| Queue query too broad (over 10,000 for bulk) | Inline message asking to narrow filters |
| Stale row after another user's change | `VERSION_CONFLICT`; row refreshes and shows "Updated by someone else" |
| Workflow start fails | Operation shows "Not started" with support reference; nothing changed |

<!-- section:performance -->
## Performance budgets

`(secretariat)` budgets: ≤ 260 KB gzip first-load JS; TTFB p75 ≤ 800 ms for queue pages; filter change to updated rows p75 ≤ 700 ms. Data table virtualises rows beyond 100 when "show more" is used; RSC payload for a queue page ≤ 200 KB. Proposed peak: 300 concurrent secretariat users per region.

<!-- section:security -->
## Security headers and browser session

Inherits defaults. Additions: step-up for bulk actions over 50 cases and for issuing documents on behalf of the tribunal; audit tab visible only to roles allowed by [[PKG-policy-engine-permission-matrix]]; CSV exports go through the export service with watermark and audit, never generated in the browser. Ethical walls ([[PKG-ethical-walls-conflict-based]]) hide walled cases from queues and counts.

<!-- section:i18n -->
## Localisation hookup

Namespace `secretariat`. Deadline columns show seat time zone; the scheduler shows each participant's local time next to the seat time.

<!-- section:observability -->
## Frontend observability

Metrics: queue load time, bulk operations started and failure ratio, task claim-to-complete time. Bulk workflows are visible to operators via `tenantId` search attribute ([[WF-separation-of-concerns-temporal]]).

<!-- section:testing -->
## Testing strategy

- Playwright: filter a queue, bulk-send reminders to 120 cases, watch the operation page; schedule a hearing with a conflict; change status with an illegal transition.
- JAWS + Chrome and NVDA + Firefox runs on the queue table and bulk dialog ([[APP-secretariat-console-and-neutral]]).
- Load test: 300 concurrent users paging a 20,000-case queue in staging.

<!-- section:questions -->
## Open questions

- [ ] Bulk limits (500 explicit IDs, 10,000 by filter) and whether SEBI ODR tenants need more (owner: CORD product)
- [ ] Should queue counts update live (server-sent events) or is 30-second freshness enough? (owner: frontend lead)
- [ ] Keyboard shortcut set for the console and how users change it (owner: UX)

<!-- checks -->
## Template checks

<!-- check:tenancy -->
### Tenant isolation in rendering and caching

Queue counts are the only cached data and are keyed by tenant, user and view. Bulk workflows carry tenant ID in the workflow ID and search attributes, and each activity opens its own tenant transaction.

<!-- check:data-exposure -->
### Server boundary and data exposure

Queue rows are view objects with only the columns the role may see; walled cases are excluded on the server, including from counts, so a count cannot reveal a hidden case.

<!-- check:resilience -->
### Failure, deploys and version skew

Bulk actions run as Temporal workflows with per-item idempotency, so closing the browser or a deploy does not stop them; the operation page can be reopened from the URL.

<!-- check:capacity -->
### Rendering cost and capacity

Server-side pagination at 50 rows, indexed allow-listed filters, and cached counts keep a 20,000-case queue within the RSC size and TTFB budgets; load test with 300 concurrent users per region before Approved.

<!-- check:accessibility -->
### App-level accessibility mechanics

The queue uses the grid pattern from [[PKG-data-table]] with sortable column headers announced, row selection by keyboard, and a polite announcement of results count after filtering; bulk dialogs state the number of affected cases in the heading.

<!-- end -->
